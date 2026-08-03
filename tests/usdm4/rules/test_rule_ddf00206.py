"""Tests for RuleDDF00206 — embedded-only AdministrableProduct must have no sourcing.

Covers:
- metadata
- _is_specified for each branch (None, empty str/list/dict, truthy primitives)
- Happy path: embedded-only AP with no sourcing → pass
- AP embedded AND administered → sourcing permitted → pass
- AP embedded-only AND has sourcing → failure
- Non-dict devices/interventions/administrations/products are skipped
"""

from unittest.mock import MagicMock

from src.usdm4.rules.library.rule_ddf00206 import RuleDDF00206, _is_specified
from src.usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# metadata
# ---------------------------------------------------------------------------


def test_metadata():
    rule = RuleDDF00206()
    assert rule._rule == "DDF00206"
    assert rule._level == RuleTemplate.ERROR
    assert "Sourcing" in rule._rule_text


# ---------------------------------------------------------------------------
# _is_specified helper — each branch
# ---------------------------------------------------------------------------


def test_is_specified_none_is_false():
    assert _is_specified(None) is False


def test_is_specified_empty_containers_are_false():
    assert _is_specified([]) is False
    assert _is_specified({}) is False
    assert _is_specified("") is False


def test_is_specified_non_empty_containers_are_true():
    assert _is_specified([1]) is True
    assert _is_specified({"a": 1}) is True
    assert _is_specified("x") is True


def test_is_specified_other_types_truthy():
    """Non-collection/non-str primitives are considered specified."""
    assert _is_specified(0) is True
    assert _is_specified(False) is True  # not None, not a listed type


# ---------------------------------------------------------------------------
# validate — main scenarios
# ---------------------------------------------------------------------------


def _data_with_versions(versions):
    data = MagicMock()
    data.instances_by_klass.side_effect = lambda klass: (
        versions if klass == "StudyVersion" else []
    )
    data.path_by_id.return_value = "$.p"
    return data


def test_embedded_only_without_sourcing_passes():
    rule = RuleDDF00206()
    data = _data_with_versions(
        [
            {
                "medicalDevices": [{"embeddedProductId": "ap1"}],
                "studyInterventions": [],
                "administrableProducts": [{"id": "ap1"}],  # no sourcing
            }
        ]
    )
    assert rule.validate({"data": data}) is True


def test_embedded_and_administered_permits_sourcing():
    rule = RuleDDF00206()
    data = _data_with_versions(
        [
            {
                "medicalDevices": [{"embeddedProductId": "ap1"}],
                "studyInterventions": [
                    {"administrations": [{"administrableProductId": "ap1"}]}
                ],
                "administrableProducts": [{"id": "ap1", "sourcing": {"x": 1}}],
            }
        ]
    )
    assert rule.validate({"data": data}) is True


def test_embedded_only_with_sourcing_fails():
    rule = RuleDDF00206()
    data = _data_with_versions(
        [
            {
                "medicalDevices": [{"embeddedProductId": "ap1"}],
                "studyInterventions": [],
                "administrableProducts": [
                    {"id": "ap1", "sourcing": {"supplier": "x"}},
                ],
            }
        ]
    )
    assert rule.validate({"data": data}) is False
    assert rule.errors().count() == 1


def test_non_embedded_ap_is_ignored():
    """AP that isn't embedded by any device isn't in scope."""
    rule = RuleDDF00206()
    data = _data_with_versions(
        [
            {
                "medicalDevices": [],
                "studyInterventions": [],
                "administrableProducts": [
                    {"id": "ap1", "sourcing": {"supplier": "x"}},
                ],
            }
        ]
    )
    assert rule.validate({"data": data}) is True


def test_non_dict_devices_interventions_and_aps_are_skipped():
    rule = RuleDDF00206()
    data = _data_with_versions(
        [
            {
                "medicalDevices": [None, "oops", {"embeddedProductId": "ap1"}],
                "studyInterventions": [
                    "bad",
                    None,
                    {"administrations": [None, "bad", {}]},
                ],
                "administrableProducts": [None, "bad", {"id": "ap1"}],
            }
        ]
    )
    # ap1 is embedded-only without sourcing → still passes
    assert rule.validate({"data": data}) is True


def test_missing_lists_default_to_empty():
    rule = RuleDDF00206()
    data = _data_with_versions([{}])  # no keys at all
    assert rule.validate({"data": data}) is True


def test_null_embedded_product_id_is_ignored():
    """A device with empty embeddedProductId shouldn't leak into the set."""
    rule = RuleDDF00206()
    data = _data_with_versions(
        [
            {
                "medicalDevices": [{"embeddedProductId": None}],
                "administrableProducts": [
                    {"id": None, "sourcing": {"s": 1}},
                ],
            }
        ]
    )
    assert rule.validate({"data": data}) is True
