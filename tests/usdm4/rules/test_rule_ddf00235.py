"""Tests for RuleDDF00235 — no unit on plannedCompletionNumber."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00235 import RuleDDF00235
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00235:
    def test_metadata(self):
        rule = RuleDDF00235()
        assert rule._rule == "DDF00235"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, populations=None, cohorts=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "StudyDesignPopulation": populations or [],
            "StudyCohort": cohorts or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_number_skipped(self):
        rule = RuleDDF00235()
        data = self._data(cohorts=[{"id": "C1"}])
        assert rule.validate({"data": data}) is True

    def test_non_dict_skipped(self):
        rule = RuleDDF00235()
        data = self._data(cohorts=[{"id": "C1", "plannedCompletionNumber": 5}])
        assert rule.validate({"data": data}) is True

    def test_quantity_unit_fails(self):
        rule = RuleDDF00235()
        data = self._data(
            populations=[{"id": "P1", "plannedCompletionNumber": {"unit": {"x": 1}}}]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_range_endpoint_unit_fails(self):
        rule = RuleDDF00235()
        data = self._data(
            cohorts=[
                {
                    "id": "C1",
                    "plannedCompletionNumber": {
                        "maxValue": {"value": 10, "unit": {"code": "X"}}
                    },
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_no_unit_passes(self):
        rule = RuleDDF00235()
        data = self._data(
            cohorts=[{"id": "C1", "plannedCompletionNumber": {"value": 50}}]
        )
        assert rule.validate({"data": data}) is True
