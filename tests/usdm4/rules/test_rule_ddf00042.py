"""Tests for RuleDDF00042 — plannedAge range should not be approximate."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00042 import RuleDDF00042
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00042:
    def test_metadata(self):
        rule = RuleDDF00042()
        assert rule._rule == "DDF00042"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, populations=None, cohorts=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "StudyDesignPopulation": populations or [],
            "StudyCohort": cohorts or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_planned_age_skipped(self):
        rule = RuleDDF00042()
        data = self._data(populations=[{"id": "P1"}])
        assert rule.validate({"data": data}) is True

    def test_non_dict_skipped(self):
        rule = RuleDDF00042()
        data = self._data(cohorts=[{"id": "C1", "plannedAge": "bad"}])
        assert rule.validate({"data": data}) is True

    def test_non_approximate_passes(self):
        rule = RuleDDF00042()
        data = self._data(
            populations=[
                {"id": "P1", "plannedAge": {"id": "R1", "isApproximate": False}}
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_approximate_fails_with_range_id(self):
        rule = RuleDDF00042()
        data = self._data(
            populations=[
                {"id": "P1", "plannedAge": {"id": "R1", "isApproximate": True}}
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_approximate_fails_without_range_id(self):
        rule = RuleDDF00042()
        data = self._data(cohorts=[{"id": "C1", "plannedAge": {"isApproximate": True}}])
        assert rule.validate({"data": data}) is False
