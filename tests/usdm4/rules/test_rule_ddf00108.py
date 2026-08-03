"""Tests for RuleDDF00108 — StudyTimeline must declare at least one exit."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00108 import RuleDDF00108
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00108:
    def test_metadata(self):
        rule = RuleDDF00108()
        assert rule._rule == "DDF00108"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_exits_present_passes(self):
        rule = RuleDDF00108()
        data = self._data([{"id": "T1", "exits": [{"id": "X1"}]}])
        assert rule.validate({"data": data}) is True

    def test_empty_exits_fails(self):
        rule = RuleDDF00108()
        data = self._data([{"id": "T1", "exits": []}])
        assert rule.validate({"data": data}) is False
        assert "No exits defined" in rule.errors().dump()

    def test_missing_exits_key_fails(self):
        rule = RuleDDF00108()
        data = self._data([{"id": "T1"}])
        assert rule.validate({"data": data}) is False
        assert "Missing exits" in rule.errors().dump()
