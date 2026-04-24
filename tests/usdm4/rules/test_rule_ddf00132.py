"""Tests for RuleDDF00132 — plannedCompletionNumber consistency (pop vs cohorts)."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00132 import RuleDDF00132
from usdm4.rules.rule_template import RuleTemplate


def _data(populations):
    data = MagicMock()
    data.instances_by_klass.return_value = populations
    data.path_by_id.return_value = "$.path"
    return data


ATTR = "plannedCompletionNumber"


class TestRuleDDF00132:
    def test_metadata(self):
        rule = RuleDDF00132()
        assert rule._rule == "DDF00132"
        assert rule._level == RuleTemplate.ERROR

    def test_population_only_passes(self):
        rule = RuleDDF00132()
        data = _data(
            [{"id": "P1", ATTR: {"value": 100}, "cohorts": [{"id": "C1"}, {"id": "C2"}]}]
        )
        assert rule.validate({"data": data}) is True

    def test_all_cohorts_only_passes(self):
        rule = RuleDDF00132()
        data = _data(
            [
                {
                    "id": "P1",
                    "cohorts": [
                        {"id": "C1", ATTR: {"value": 1}},
                        {"id": "C2", ATTR: {"value": 2}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_nothing_specified_passes(self):
        """DDF text starts 'if a planned completion number is defined' —
        if nowhere defined, there's nothing to check."""
        rule = RuleDDF00132()
        data = _data([{"id": "P1", "cohorts": [{"id": "C1"}, {"id": "C2"}]}])
        assert rule.validate({"data": data}) is True

    def test_population_and_some_cohorts_fails(self):
        rule = RuleDDF00132()
        data = _data(
            [
                {
                    "id": "P1",
                    ATTR: {"value": 100},
                    "cohorts": [
                        {"id": "C1", ATTR: {"value": 50}},
                        {"id": "C2"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "specified on the study population and on" in rule.errors().dump()

    def test_subset_of_cohorts_only_fails(self):
        rule = RuleDDF00132()
        data = _data(
            [
                {
                    "id": "P1",
                    "cohorts": [
                        {"id": "C1", ATTR: {"value": 1}},
                        {"id": "C2"},
                        {"id": "C3"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "specified on only 1 of 3" in rule.errors().dump()

    def test_no_cohorts_population_only_passes(self):
        rule = RuleDDF00132()
        data = _data([{"id": "P1", ATTR: {"value": 100}, "cohorts": []}])
        assert rule.validate({"data": data}) is True

    def test_empty_dict_value_treated_as_not_specified(self):
        rule = RuleDDF00132()
        data = _data([{"id": "P1", ATTR: {}, "cohorts": []}])
        assert rule.validate({"data": data}) is True
