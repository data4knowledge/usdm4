"""Tests for RuleDDF00098 — plannedSex required on pop or all cohorts."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00098 import RuleDDF00098
from usdm4.rules.rule_template import RuleTemplate


def _data(populations):
    data = MagicMock()
    data.instances_by_klass.return_value = populations
    data.path_by_id.return_value = "$.path"
    return data


ATTR = "plannedSex"


class TestRuleDDF00098:
    def test_metadata(self):
        rule = RuleDDF00098()
        assert rule._rule == "DDF00098"
        assert rule._level == RuleTemplate.ERROR

    def test_population_only_passes(self):
        rule = RuleDDF00098()
        data = _data([{"id": "P1", ATTR: [{"code": "A"}], "cohorts": [{"id": "C1"}]}])
        assert rule.validate({"data": data}) is True

    def test_population_only_no_cohorts_passes(self):
        rule = RuleDDF00098()
        data = _data([{"id": "P1", ATTR: [{"code": "A"}], "cohorts": []}])
        assert rule.validate({"data": data}) is True

    def test_all_cohorts_only_passes(self):
        rule = RuleDDF00098()
        data = _data(
            [
                {
                    "id": "P1",
                    "cohorts": [
                        {"id": "C1", ATTR: [{"code": "A"}]},
                        {"id": "C2", ATTR: [{"code": "B"}]},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_nothing_anywhere_fails(self):
        """Regression: DDF00098 has no 'if defined' clause. Not specifying
        anywhere is a failure."""
        rule = RuleDDF00098()
        data = _data([{"id": "P1", "cohorts": [{"id": "C1"}]}])
        assert rule.validate({"data": data}) is False
        assert "not specified on the study population" in rule.errors().dump()

    def test_nothing_anywhere_no_cohorts_fails(self):
        rule = RuleDDF00098()
        data = _data([{"id": "P1", "cohorts": []}])
        assert rule.validate({"data": data}) is False

    def test_population_and_some_cohorts_fails(self):
        rule = RuleDDF00098()
        data = _data(
            [
                {
                    "id": "P1",
                    ATTR: [{"code": "A"}],
                    "cohorts": [
                        {"id": "C1", ATTR: [{"code": "A"}]},
                        {"id": "C2"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "specified on the study population and on" in rule.errors().dump()

    def test_subset_of_cohorts_only_fails(self):
        rule = RuleDDF00098()
        data = _data(
            [
                {
                    "id": "P1",
                    "cohorts": [
                        {"id": "C1", ATTR: [{"code": "A"}]},
                        {"id": "C2"},
                        {"id": "C3"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "specified on only 1 of 3" in rule.errors().dump()

    def test_empty_list_value_treated_as_not_specified(self):
        rule = RuleDDF00098()
        data = _data([{"id": "P1", ATTR: [], "cohorts": []}])
        # Empty list = not specified + no cohorts = nothing anywhere → FAIL
        assert rule.validate({"data": data}) is False
