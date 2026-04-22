"""Tests for RuleDDF00194 — Address requires at least one attribute."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00194 import RuleDDF00194
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00194:
    def test_metadata(self):
        rule = RuleDDF00194()
        assert rule._rule == "DDF00194"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_populated_passes(self):
        rule = RuleDDF00194()
        data = self._data([{"id": "A1", "city": "Boston"}])
        assert rule.validate({"data": data}) is True

    def test_empty_fails(self):
        rule = RuleDDF00194()
        data = self._data([{"id": "A1"}])
        assert rule.validate({"data": data}) is False
        assert "at least one required" in rule.errors().dump()

    def test_all_falsy_fails(self):
        rule = RuleDDF00194()
        data = self._data(
            [{"id": "A1", "text": "", "lines": [], "city": None, "country": None}]
        )
        assert rule.validate({"data": data}) is False
