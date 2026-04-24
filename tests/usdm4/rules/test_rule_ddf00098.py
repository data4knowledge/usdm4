"""Tests for RuleDDF00098 — plannedSex must be populated."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00098 import RuleDDF00098
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00098:
    def test_metadata(self):
        rule = RuleDDF00098()
        assert rule._rule == "DDF00098"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_populated_passes(self):
        rule = RuleDDF00098()
        data = self._data([{"id": "P1", "plannedSex": [{"code": "C1"}]}])
        assert rule.validate({"data": data}) is True

    def test_missing_fails(self):
        rule = RuleDDF00098()
        data = self._data([{"id": "P1"}])
        assert rule.validate({"data": data}) is False
        assert "missing or empty" in rule.errors().dump()
