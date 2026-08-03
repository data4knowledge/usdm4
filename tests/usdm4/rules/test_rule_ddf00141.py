"""Tests for RuleDDF00141 — plannedSex CT check on SDP + StudyCohort."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00141 import RuleDDF00141
from usdm4.rules.rule_template import RuleTemplate


def _ct_with(codes_decodes):
    ct = MagicMock()
    ct.klass_and_attribute.return_value = {
        "terms": [{"conceptId": c, "preferredTerm": d} for c, d in codes_decodes]
    }
    return ct


def _data_for(instances_by_klass):
    data = MagicMock()
    data.instances_by_klass.side_effect = lambda k: instances_by_klass.get(k, [])
    data.path_by_id.return_value = "$.path"
    return data


class TestRuleDDF00141:
    def test_metadata(self):
        rule = RuleDDF00141()
        assert rule._rule == "DDF00141"
        assert rule._level == RuleTemplate.ERROR

    def test_both_sides_valid_pass(self):
        rule = RuleDDF00141()
        ct = _ct_with([("A", "DA")])
        data = _data_for(
            {
                "StudyDesignPopulation": [
                    {"id": "P1", "plannedSex": [{"code": "A", "decode": "DA"}]}
                ],
                "StudyCohort": [
                    {"id": "C1", "plannedSex": [{"code": "A", "decode": "DA"}]}
                ],
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is True

    def test_cohort_invalid_fails_even_if_population_valid(self):
        """Regression: previous `pop_result or cohort_result` hid cohort failures.

        The population side returns True (codes match) but the cohort side
        has an invalid code. The rule MUST report Failure, not Success.
        """
        rule = RuleDDF00141()
        ct = _ct_with([("A", "DA")])
        data = _data_for(
            {
                "StudyDesignPopulation": [
                    {"id": "P1", "plannedSex": [{"code": "A", "decode": "DA"}]}
                ],
                "StudyCohort": [
                    {"id": "C1", "plannedSex": [{"code": "BAD", "decode": "DA"}]}
                ],
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False
        assert rule.errors().count() >= 1

    def test_population_invalid_fails_even_if_cohort_valid(self):
        rule = RuleDDF00141()
        ct = _ct_with([("A", "DA")])
        data = _data_for(
            {
                "StudyDesignPopulation": [
                    {"id": "P1", "plannedSex": [{"code": "BAD", "decode": "DA"}]}
                ],
                "StudyCohort": [
                    {"id": "C1", "plannedSex": [{"code": "A", "decode": "DA"}]}
                ],
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False

    def test_both_sides_invalid_accumulate(self):
        rule = RuleDDF00141()
        ct = _ct_with([("A", "DA")])
        data = _data_for(
            {
                "StudyDesignPopulation": [
                    {"id": "P1", "plannedSex": [{"code": "X", "decode": "DA"}]}
                ],
                "StudyCohort": [
                    {"id": "C1", "plannedSex": [{"code": "Y", "decode": "DA"}]}
                ],
            }
        )
        assert rule.validate({"data": data, "ct": ct}) is False
        # Each side contributes at least one failure.
        assert rule.errors().count() >= 2
