"""Tests for RuleDDF00237 — plannedAge unit must come from C66781 codelist.

Covers:
- metadata
- C66781 missing from CT cache → rule skipped (returns True)
- Quantity-shaped plannedAge (with 'value')
- Range-shaped plannedAge (minValue/maxValue)
- Non-dict plannedAge early-return
- Non-dict endpoint ignored inside Range
- Missing/None unit → skipped
- unit without standardCode → failure
- Invalid code → failure
- Valid code but invalid decode → failure
- Valid code + valid decode → pass
- Both StudyDesignPopulation and StudyCohort are scanned
"""

from unittest.mock import MagicMock

from src.usdm4.rules.library.rule_ddf00237 import (
    RuleDDF00237,
    _iter_quantities,
    AGE_UNIT_CODELIST,
)
from src.usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# metadata
# ---------------------------------------------------------------------------


def test_metadata():
    rule = RuleDDF00237()
    assert rule._rule == "DDF00237"
    assert rule._level == RuleTemplate.ERROR
    assert "Age Unit" in rule._rule_text


# ---------------------------------------------------------------------------
# _iter_quantities helper
# ---------------------------------------------------------------------------


def test_iter_quantities_non_dict_yields_nothing():
    assert list(_iter_quantities(None)) == []
    assert list(_iter_quantities("oops")) == []


def test_iter_quantities_quantity_shape():
    q = {"value": 18, "unit": {}}
    assert list(_iter_quantities(q)) == [q]


def test_iter_quantities_range_shape_yields_endpoints():
    min_q = {"unit": {}}
    max_q = {"unit": {}}
    out = list(_iter_quantities({"minValue": min_q, "maxValue": max_q}))
    assert out == [min_q, max_q]


def test_iter_quantities_range_ignores_non_dict_endpoints():
    out = list(_iter_quantities({"minValue": None, "maxValue": "oops"}))
    assert out == []


# ---------------------------------------------------------------------------
# validate() — codelist missing
# ---------------------------------------------------------------------------


def test_validate_returns_true_when_codelist_missing():
    rule = RuleDDF00237()
    ct = MagicMock()
    ct._by_code_list = {}  # C66781 absent
    data = MagicMock()
    assert rule.validate({"data": data, "ct": ct}) is True
    # No instances queried because we bail early
    data.instances_by_klass.assert_not_called()


# ---------------------------------------------------------------------------
# validate() — failure paths
# ---------------------------------------------------------------------------


def _ct_with_age_unit():
    """CT stub with C66781 populated."""
    ct = MagicMock()
    ct._by_code_list = {
        AGE_UNIT_CODELIST: {
            "terms": [
                {"conceptId": "C29848", "preferredTerm": "Years"},
                {"conceptId": "C25301", "preferredTerm": "Months"},
            ]
        }
    }
    return ct


def _data_with_instances(pop_instances=None, cohort_instances=None):
    data = MagicMock()

    def _by_klass(klass):
        if klass == "StudyDesignPopulation":
            return pop_instances or []
        if klass == "StudyCohort":
            return cohort_instances or []
        return []

    data.instances_by_klass.side_effect = _by_klass
    data.path_by_id.return_value = "$.x"
    return data


def test_quantity_without_standard_code_raises_failure():
    rule = RuleDDF00237()
    ct = _ct_with_age_unit()
    data = _data_with_instances(
        pop_instances=[
            {
                "id": "p1",
                "plannedAge": {"value": 18, "unit": {"code": "X"}},  # no standardCode
            }
        ]
    )
    assert rule.validate({"data": data, "ct": ct}) is False
    assert rule.errors().count() == 1


def test_quantity_with_invalid_code_raises_failure():
    rule = RuleDDF00237()
    ct = _ct_with_age_unit()
    data = _data_with_instances(
        pop_instances=[
            {
                "id": "p1",
                "plannedAge": {
                    "value": 18,
                    "unit": {"standardCode": {"code": "BOGUS", "decode": "Nonsense"}},
                },
            }
        ]
    )
    assert rule.validate({"data": data, "ct": ct}) is False
    assert rule.errors().count() == 1


def test_quantity_with_valid_code_valid_decode_passes():
    rule = RuleDDF00237()
    ct = _ct_with_age_unit()
    data = _data_with_instances(
        pop_instances=[
            {
                "id": "p1",
                "plannedAge": {
                    "value": 18,
                    "unit": {"standardCode": {"code": "C29848", "decode": "Years"}},
                },
            }
        ]
    )
    assert rule.validate({"data": data, "ct": ct}) is True
    assert rule.errors().count() == 0


def test_quantity_with_valid_code_but_wrong_decode_raises_failure():
    rule = RuleDDF00237()
    ct = _ct_with_age_unit()
    data = _data_with_instances(
        pop_instances=[
            {
                "id": "p1",
                "plannedAge": {
                    "value": 18,
                    "unit": {"standardCode": {"code": "C29848", "decode": "Typod"}},
                },
            }
        ]
    )
    assert rule.validate({"data": data, "ct": ct}) is False


def test_unit_absent_is_skipped():
    rule = RuleDDF00237()
    ct = _ct_with_age_unit()
    data = _data_with_instances(
        pop_instances=[
            {"id": "p1", "plannedAge": {"value": 18, "unit": None}},
        ]
    )
    assert rule.validate({"data": data, "ct": ct}) is True


def test_range_shape_validates_each_endpoint():
    rule = RuleDDF00237()
    ct = _ct_with_age_unit()
    data = _data_with_instances(
        pop_instances=[
            {
                "id": "p1",
                "plannedAge": {
                    "minValue": {
                        "unit": {"standardCode": {"code": "BOGUS", "decode": "X"}}
                    },
                    "maxValue": {
                        "unit": {"standardCode": {"code": "C29848", "decode": "Years"}}
                    },
                },
            }
        ]
    )
    assert rule.validate({"data": data, "ct": ct}) is False
    # Only the min endpoint fails; max is valid
    assert rule.errors().count() == 1


def test_cohort_scope_also_scanned():
    rule = RuleDDF00237()
    ct = _ct_with_age_unit()
    data = _data_with_instances(
        cohort_instances=[
            {
                "id": "c1",
                "plannedAge": {
                    "value": 18,
                    "unit": {"standardCode": {"code": "WRONG", "decode": "Years"}},
                },
            }
        ]
    )
    assert rule.validate({"data": data, "ct": ct}) is False
    assert rule.errors().count() == 1


def test_planned_age_missing_is_skipped():
    rule = RuleDDF00237()
    ct = _ct_with_age_unit()
    data = _data_with_instances(pop_instances=[{"id": "p1"}])  # no plannedAge
    assert rule.validate({"data": data, "ct": ct}) is True
    assert rule.errors().count() == 0


def test_codelist_with_null_terms_falls_back_to_empty():
    """terms: None should not crash — treated as empty codelist."""
    rule = RuleDDF00237()
    ct = MagicMock()
    ct._by_code_list = {AGE_UNIT_CODELIST: {"terms": None}}
    data = _data_with_instances(
        pop_instances=[
            {
                "id": "p1",
                "plannedAge": {
                    "value": 18,
                    "unit": {"standardCode": {"code": "C29848"}},
                },
            }
        ]
    )
    # No valid codes → any code is rejected
    assert rule.validate({"data": data, "ct": ct}) is False
