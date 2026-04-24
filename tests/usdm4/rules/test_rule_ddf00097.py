"""Tests for RuleDDF00097 — plannedAge must be populated."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00097 import RuleDDF00097
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00097:
    def test_metadata(self):
        rule = RuleDDF00097()
        assert rule._rule == "DDF00097"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_populated_passes(self):
        rule = RuleDDF00097()
        data = self._data([{"id": "P1", "plannedAge": {"minValue": 18}}])
        assert rule.validate({"data": data}) is True

    def test_missing_fails(self):
        rule = RuleDDF00097()
        data = self._data([{"id": "P1"}])
        assert rule.validate({"data": data}) is False
        assert "missing or empty" in rule.errors().dump()
