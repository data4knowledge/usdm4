"""Tests for RuleDDF00041 — Endpoint.level must be populated."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00041 import RuleDDF00041
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00041:
    def test_metadata(self):
        rule = RuleDDF00041()
        assert rule._rule == "DDF00041"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_level_populated_passes(self):
        rule = RuleDDF00041()
        data = self._data([{"id": "E1", "level": {"code": "C1"}}])
        assert rule.validate({"data": data}) is True

    def test_missing_fails(self):
        rule = RuleDDF00041()
        data = self._data([{"id": "E1"}])
        assert rule.validate({"data": data}) is False
        assert "missing or empty" in rule.errors().dump()
