"""Tests for RuleDDF00097 — plannedAge required on pop or all cohorts."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00097 import RuleDDF00097
from usdm4.rules.rule_template import RuleTemplate


def _data(populations):
    data = MagicMock()
    data.instances_by_klass.return_value = populations
    data.path_by_id.return_value = "$.path"
    return data


ATTR = "plannedAge"


class TestRuleDDF00097:
    def test_metadata(self):
        rule = RuleDDF00097()
        assert rule._rule == "DDF00097"
        assert rule._level == RuleTemplate.ERROR

    def test_population_only_passes(self):
        rule = RuleDDF00097()
        data = _data(
            [{"id": "P1", ATTR: {"minValue": 18}, "cohorts": [{"id": "C1"}]}]
        )
        assert rule.validate({"data": data}) is True

    def test_population_only_no_cohorts_passes(self):
        rule = RuleDDF00097()
        data = _data([{"id": "P1", ATTR: {"minValue": 18}, "cohorts": []}])
        assert rule.validate({"data": data}) is True

    def test_all_cohorts_only_passes(self):
        rule = RuleDDF00097()
        data = _data(
            [
                {
                    "id": "P1",
                    "cohorts": [
                        {"id": "C1", ATTR: {"minValue": 18}},
                        {"id": "C2", ATTR: {"minValue": 65}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_nothing_anywhere_fails(self):
        """Regression: DDF00097 has no 'if defined' clause (unlike 132/133).
        Not specifying the value anywhere is itself a failure."""
        rule = RuleDDF00097()
        data = _data([{"id": "P1", "cohorts": [{"id": "C1"}, {"id": "C2"}]}])
        assert rule.validate({"data": data}) is False
        assert "not specified on the study population" in rule.errors().dump()

    def test_nothing_anywhere_no_cohorts_fails(self):
        rule = RuleDDF00097()
        data = _data([{"id": "P1", "cohorts": []}])
        assert rule.validate({"data": data}) is False

    def test_population_and_some_cohorts_fails(self):
        rule = RuleDDF00097()
        data = _data(
            [
                {
                    "id": "P1",
                    ATTR: {"minValue": 18},
                    "cohorts": [
                        {"id": "C1", ATTR: {"minValue": 21}},
                        {"id": "C2"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "specified on the study population and on" in rule.errors().dump()

    def test_subset_of_cohorts_only_fails(self):
        rule = RuleDDF00097()
        data = _data(
            [
                {
                    "id": "P1",
                    "cohorts": [
                        {"id": "C1", ATTR: {"minValue": 18}},
                        {"id": "C2"},
                        {"id": "C3"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "specified on only 1 of 3" in rule.errors().dump()

    def test_empty_dict_value_treated_as_not_specified(self):
        rule = RuleDDF00097()
        data = _data([{"id": "P1", ATTR: {}, "cohorts": []}])
        # Empty dict on pop and no cohorts → nothing anywhere → FAIL
        assert rule.validate({"data": data}) is False
