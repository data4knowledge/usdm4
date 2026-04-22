"""Tests for RuleDDF00242 — Range.minValue populated."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00242 import RuleDDF00242
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00242:
    def test_metadata(self):
        rule = RuleDDF00242()
        assert rule._rule == "DDF00242"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_populated_passes(self):
        rule = RuleDDF00242()
        data = self._data([{"id": "R1", "minValue": 1}])
        assert rule.validate({"data": data}) is True

    def test_empty_fails(self):
        rule = RuleDDF00242()
        data = self._data([{"id": "R1"}])
        assert rule.validate({"data": data}) is False
