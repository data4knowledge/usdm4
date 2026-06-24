"""Tests for RuleDDF00237 — plannedAge unit must come from C66781 codelist.

Covers:
- metadata
- C66781 not loaded → predicate raises MissingCodelistError (no skip)
- Quantity-shaped plannedAge (with 'value')
- Range-shaped plannedAge (minValue/maxValue)
- Non-dict plannedAge early-return
- Non-dict endpoint ignored inside Range
- Missing/None unit → skipped
- unit without standardCode → failure
- Invalid code → failure
- Valid code but invalid decode → failure
- Valid code + valid decode → pass (matching preferredTerm or submissionValue)
- Both StudyDesignPopulation and StudyCohort are scanned
- Extensions (via source-tagged terms) transparently accepted
"""

import pytest
from unittest.mock import MagicMock

from usdm4.ct.cdisc.library import MissingCodelistError
from usdm4.rules.library.rule_ddf00237 import (
    RuleDDF00237,
    _iter_quantities,
    AGE_UNIT_CODELIST,
)
from usdm4.rules.rule_template import RuleTemplate

from tests.usdm4.rules.ct_helpers import FakeCT


def _ct_with_age_unit() -> FakeCT:
    return FakeCT(
        {
            AGE_UNIT_CODELIST: [
                {
                    "conceptId": "C29848",
                    "preferredTerm": "Years",
                    "submissionValue": "Years",
                },
                {
                    "conceptId": "C25301",
                    "preferredTerm": "Months",
                    "submissionValue": "Months",
                },
            ]
        }
    )


def _ct_with_both_labels() -> FakeCT:
    """C66781 stub where preferredTerm and submissionValue differ for a
    term, so we can confirm both forms are accepted independently."""
    return FakeCT(
        {
            AGE_UNIT_CODELIST: [
                {
                    "conceptId": "C29848",
                    "preferredTerm": "Year",
                    "submissionValue": "Years",
                },
            ]
        }
    )


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
# validate() — codelist not loaded
# ---------------------------------------------------------------------------


def test_validate_raises_when_codelist_not_loaded():
    """When C66781 isn't loaded, the predicate raises MissingCodelistError.
    The rule engine surfaces this as an EXCEPTION outcome — the operator
    sees the config flaw rather than every unit silently marked valid.
    See ``feedback_missing_codelist_must_raise``."""
    rule = RuleDDF00237()
    ct = FakeCT({})  # C66781 absent
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
    with pytest.raises(MissingCodelistError, match="not loaded"):
        rule.validate({"data": data, "ct": ct})


# ---------------------------------------------------------------------------
# validate() — failure paths
# ---------------------------------------------------------------------------


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


def test_codelist_loaded_but_empty_raises():
    """A codelist loaded with zero terms is a config flaw, same shape
    as 'not loaded' — the predicate raises MissingCodelistError. The
    rule no longer treats this as 'reject every code' (which would
    flood findings) nor as 'skip silently' (which would hide the bug)."""
    rule = RuleDDF00237()
    ct = FakeCT({AGE_UNIT_CODELIST: []})
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
    with pytest.raises(MissingCodelistError, match="no terms"):
        rule.validate({"data": data, "ct": ct})


# ---------------------------------------------------------------------------
# decode accepts BOTH preferredTerm and submissionValue (same CDISC policy
# as RuleTemplate._codes_and_decodes — preserved via the by="any" mode of
# the predicate).
# ---------------------------------------------------------------------------


def test_quantity_with_decode_matching_preferred_term_passes():
    rule = RuleDDF00237()
    data = _data_with_instances(
        pop_instances=[
            {
                "id": "p1",
                "plannedAge": {
                    "value": 18,
                    "unit": {"standardCode": {"code": "C29848", "decode": "Year"}},
                },
            }
        ]
    )
    assert rule.validate({"data": data, "ct": _ct_with_both_labels()}) is True
    assert rule.errors().count() == 0


def test_quantity_with_decode_matching_submission_value_passes():
    """Regression: submissionValue must validate, not just preferredTerm."""
    rule = RuleDDF00237()
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
    assert rule.validate({"data": data, "ct": _ct_with_both_labels()}) is True
    assert rule.errors().count() == 0


def test_quantity_with_decode_matching_neither_label_still_fails():
    rule = RuleDDF00237()
    data = _data_with_instances(
        pop_instances=[
            {
                "id": "p1",
                "plannedAge": {
                    "value": 18,
                    "unit": {
                        "standardCode": {"code": "C29848", "decode": "Yr"}
                    },  # neither preferredTerm nor submissionValue
                },
            }
        ]
    )
    assert rule.validate({"data": data, "ct": _ct_with_both_labels()}) is False
    assert rule.errors().count() == 1


# ---------------------------------------------------------------------------
# Extension transparency — proof that the predicate seam works for the
# very reason we built it.
# ---------------------------------------------------------------------------


def test_extension_term_is_accepted_transparently():
    """A term added to C66781 via the extension mechanism (carrying a
    non-cdisc source tag) is accepted by DDF00237 with no rule change."""
    rule = RuleDDF00237()
    ct = FakeCT(
        {
            AGE_UNIT_CODELIST: [
                # Standard CDISC term
                {
                    "conceptId": "C29848",
                    "preferredTerm": "Years",
                    "submissionValue": "Years",
                },
                # Extension term (would be tagged with source: NCIt-M11 by
                # Library._merge_extension; the rule doesn't care about the
                # tag, only about membership).
                {
                    "conceptId": "C99999",
                    "preferredTerm": "Femtoseconds",
                    "submissionValue": "Femtoseconds",
                    "source": "NCIt-Something",
                },
            ]
        }
    )
    data = _data_with_instances(
        pop_instances=[
            {
                "id": "p1",
                "plannedAge": {
                    "value": 1,
                    "unit": {
                        "standardCode": {"code": "C99999", "decode": "Femtoseconds"}
                    },
                },
            }
        ]
    )
    assert rule.validate({"data": data, "ct": ct}) is True
    assert rule.errors().count() == 0
