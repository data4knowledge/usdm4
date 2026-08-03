"""Tests for RuleDDF00188 — plannedSex must be subset of {male, female}."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00188 import RuleDDF00188
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00188:
    def test_metadata(self):
        rule = RuleDDF00188()
        assert rule._rule == "DDF00188"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, populations=None, cohorts=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "StudyDesignPopulation": populations or [],
            "StudyCohort": cohorts or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_empty_skipped(self):
        rule = RuleDDF00188()
        data = self._data(populations=[{"id": "P1"}])
        assert rule.validate({"data": data}) is True

    def test_male_only_passes(self):
        rule = RuleDDF00188()
        data = self._data(
            populations=[{"id": "P1", "plannedSex": [{"code": "C20197"}]}]
        )
        assert rule.validate({"data": data}) is True

    def test_both_passes(self):
        rule = RuleDDF00188()
        data = self._data(
            cohorts=[
                {"id": "C1", "plannedSex": [{"code": "C16576"}, {"code": "C20197"}]}
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00188()
        data = self._data(
            populations=[
                {"id": "P1", "plannedSex": [{"code": "C20197"}, {"code": "C20197"}]}
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "duplicate entries" in rule.errors().dump()

    def test_bad_code_fails(self):
        rule = RuleDDF00188()
        data = self._data(populations=[{"id": "P1", "plannedSex": [{"code": "BAD"}]}])
        assert rule.validate({"data": data}) is False
        assert "other than Male" in rule.errors().dump()
