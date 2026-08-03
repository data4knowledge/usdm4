"""Tests for RuleDDF00232 — ObservationalStudyDesign.studyPhase must decode to NOT APPLICABLE.

Covers:
- metadata
- _phase_decode helper: non-dict phase, missing standardCode, valid decode
- studyPhase missing → failure (no decode)
- decode mismatched → failure
- decode matches (case-insensitive / whitespace-tolerant) → pass
"""

from unittest.mock import MagicMock

from src.usdm4.rules.library.rule_ddf00232 import RuleDDF00232, _phase_decode
from src.usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# metadata
# ---------------------------------------------------------------------------


def test_metadata():
    rule = RuleDDF00232()
    assert rule._rule == "DDF00232"
    assert rule._level == RuleTemplate.WARNING


# ---------------------------------------------------------------------------
# _phase_decode helper
# ---------------------------------------------------------------------------


def test_phase_decode_non_dict_returns_none():
    assert _phase_decode({"studyPhase": None}) is None
    assert _phase_decode({"studyPhase": "oops"}) is None


def test_phase_decode_missing_standard_code_returns_none():
    assert _phase_decode({"studyPhase": {}}) is None
    assert _phase_decode({"studyPhase": {"standardCode": None}}) is None


def test_phase_decode_valid():
    design = {"studyPhase": {"standardCode": {"decode": "Not Applicable"}}}
    assert _phase_decode(design) == "Not Applicable"


# ---------------------------------------------------------------------------
# validate()
# ---------------------------------------------------------------------------


def _data_with_designs(designs):
    data = MagicMock()
    data.instances_by_klass.side_effect = lambda klass: (
        designs if klass == "ObservationalStudyDesign" else []
    )
    data.path_by_id.return_value = "$.design"
    return data


def test_missing_study_phase_fails():
    rule = RuleDDF00232()
    data = _data_with_designs([{"id": "d1"}])  # no studyPhase
    assert rule.validate({"data": data}) is False
    assert rule.errors().count() == 1


def test_wrong_decode_fails():
    rule = RuleDDF00232()
    data = _data_with_designs(
        [
            {
                "id": "d1",
                "studyPhase": {"standardCode": {"decode": "Phase II"}},
            }
        ]
    )
    assert rule.validate({"data": data}) is False
    assert rule.errors().count() == 1


def test_not_applicable_passes():
    rule = RuleDDF00232()
    data = _data_with_designs(
        [
            {
                "id": "d1",
                "studyPhase": {"standardCode": {"decode": "Not Applicable"}},
            }
        ]
    )
    assert rule.validate({"data": data}) is True


def test_upper_case_not_applicable_passes():
    rule = RuleDDF00232()
    data = _data_with_designs(
        [
            {
                "id": "d1",
                "studyPhase": {"standardCode": {"decode": "NOT APPLICABLE"}},
            }
        ]
    )
    assert rule.validate({"data": data}) is True


def test_whitespace_padded_not_applicable_passes():
    rule = RuleDDF00232()
    data = _data_with_designs(
        [
            {
                "id": "d1",
                "studyPhase": {"standardCode": {"decode": "  Not Applicable  "}},
            }
        ]
    )
    assert rule.validate({"data": data}) is True


def test_no_observational_designs_passes():
    rule = RuleDDF00232()
    data = _data_with_designs([])
    assert rule.validate({"data": data}) is True
