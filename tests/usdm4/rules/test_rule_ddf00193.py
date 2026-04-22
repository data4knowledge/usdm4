"""Tests for RuleDDF00193 — masking required when blinding is not open label / double blind.

Covers:
- metadata
- _blinding_code: non-dict schema, missing standardCode, valid standardCode
- Skip paths: blinding is open label (C49659) / double blind (C15228) / None
- Applicable role with isMasked=True → pass
- Applicable role without isMasked → failure
- No applicable role (appliesToIds doesn't include sv/design) → failure
- Non-dict design / non-dict role skipped
"""

from unittest.mock import MagicMock

from src.usdm4.rules.library.rule_ddf00193 import (
    RuleDDF00193,
    _blinding_code,
    OPEN_LABEL_CODE,
    DOUBLE_BLIND_CODE,
)
from src.usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# metadata
# ---------------------------------------------------------------------------


def test_metadata():
    rule = RuleDDF00193()
    assert rule._rule == "DDF00193"
    assert rule._level == RuleTemplate.WARNING


# ---------------------------------------------------------------------------
# _blinding_code helper
# ---------------------------------------------------------------------------


def test_blinding_code_non_dict_returns_none():
    assert _blinding_code({"blindingSchema": None}) is None
    assert _blinding_code({"blindingSchema": "oops"}) is None


def test_blinding_code_missing_standard_code_returns_none():
    assert _blinding_code({"blindingSchema": {"x": 1}}) is None
    assert _blinding_code({"blindingSchema": {"standardCode": None}}) is None


def test_blinding_code_valid_returns_code():
    design = {"blindingSchema": {"standardCode": {"code": "C123"}}}
    assert _blinding_code(design) == "C123"


# ---------------------------------------------------------------------------
# validate() — each branch
# ---------------------------------------------------------------------------


def _data_with_versions(versions):
    data = MagicMock()
    data.instances_by_klass.side_effect = lambda klass: (
        versions if klass == "StudyVersion" else []
    )
    data.path_by_id.return_value = "$.design"
    return data


def _design(code=None, design_id="d1"):
    d = {"id": design_id}
    if code is not None:
        d["blindingSchema"] = {"standardCode": {"code": code}}
    return d


def test_open_label_is_skipped():
    rule = RuleDDF00193()
    data = _data_with_versions(
        [{"id": "sv1", "studyDesigns": [_design(OPEN_LABEL_CODE)], "roles": []}]
    )
    assert rule.validate({"data": data}) is True


def test_double_blind_is_skipped():
    rule = RuleDDF00193()
    data = _data_with_versions(
        [{"id": "sv1", "studyDesigns": [_design(DOUBLE_BLIND_CODE)], "roles": []}]
    )
    assert rule.validate({"data": data}) is True


def test_no_blinding_code_is_skipped():
    rule = RuleDDF00193()
    data = _data_with_versions(
        [{"id": "sv1", "studyDesigns": [{"id": "d1"}], "roles": []}]
    )
    assert rule.validate({"data": data}) is True


def test_non_dict_design_is_skipped():
    rule = RuleDDF00193()
    data = _data_with_versions(
        [{"id": "sv1", "studyDesigns": [None, "bad"], "roles": []}]
    )
    assert rule.validate({"data": data}) is True


def test_applicable_role_with_masked_passes():
    rule = RuleDDF00193()
    data = _data_with_versions(
        [
            {
                "id": "sv1",
                "studyDesigns": [_design("C12345")],  # single-blind-ish code
                "roles": [
                    {"appliesToIds": ["d1"], "masking": {"isMasked": True}},
                ],
            }
        ]
    )
    assert rule.validate({"data": data}) is True


def test_no_masked_role_fails():
    rule = RuleDDF00193()
    data = _data_with_versions(
        [
            {
                "id": "sv1",
                "studyDesigns": [_design("C12345")],
                "roles": [
                    {"appliesToIds": ["d1"], "masking": {"isMasked": False}},
                ],
            }
        ]
    )
    assert rule.validate({"data": data}) is False
    assert rule.errors().count() == 1


def test_role_without_applies_to_is_skipped_and_failure_raised():
    """If no role applies to sv/design, no masked role → failure."""
    rule = RuleDDF00193()
    data = _data_with_versions(
        [
            {
                "id": "sv1",
                "studyDesigns": [_design("C12345")],
                "roles": [
                    {"appliesToIds": ["other"], "masking": {"isMasked": True}},
                ],
            }
        ]
    )
    assert rule.validate({"data": data}) is False


def test_non_dict_roles_are_skipped():
    rule = RuleDDF00193()
    data = _data_with_versions(
        [
            {
                "id": "sv1",
                "studyDesigns": [_design("C12345")],
                "roles": [None, "bad", {"appliesToIds": ["d1"], "masking": None}],
            }
        ]
    )
    # masking is None → not masked → failure
    assert rule.validate({"data": data}) is False


def test_role_applies_to_sv_id_counts():
    """Role with sv's id in appliesToIds is also applicable."""
    rule = RuleDDF00193()
    data = _data_with_versions(
        [
            {
                "id": "sv1",
                "studyDesigns": [_design("C12345")],
                "roles": [
                    {"appliesToIds": ["sv1"], "masking": {"isMasked": True}},
                ],
            }
        ]
    )
    assert rule.validate({"data": data}) is True
