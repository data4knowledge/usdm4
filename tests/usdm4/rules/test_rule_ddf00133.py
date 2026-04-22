"""Tests for RuleDDF00133 — plannedEnrollmentNumber populated."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00133 import RuleDDF00133
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00133:
    def test_metadata(self):
        rule = RuleDDF00133()
        assert rule._rule == "DDF00133"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_populated_passes(self):
        rule = RuleDDF00133()
        data = self._data([{"id": "P1", "plannedEnrollmentNumber": {"value": 50}}])
        assert rule.validate({"data": data}) is True

    def test_missing_fails(self):
        rule = RuleDDF00133()
        data = self._data([{"id": "P1"}])
        assert rule.validate({"data": data}) is False
