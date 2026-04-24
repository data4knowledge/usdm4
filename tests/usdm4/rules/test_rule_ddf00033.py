"""Tests for RuleDDF00033 — Duration text or quantity required."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00033 import RuleDDF00033
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00033:
    def test_metadata(self):
        rule = RuleDDF00033()
        assert rule._rule == "DDF00033"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, durations):
        data = MagicMock()
        data.instances_by_klass.return_value = durations
        data.path_by_id.return_value = "$.path"
        return data

    def test_text_passes(self):
        rule = RuleDDF00033()
        data = self._data([{"id": "D1", "text": "1 day"}])
        assert rule.validate({"data": data}) is True

    def test_quantity_passes(self):
        rule = RuleDDF00033()
        data = self._data([{"id": "D1", "quantity": {"value": 1}}])
        assert rule.validate({"data": data}) is True

    def test_neither_fails(self):
        rule = RuleDDF00033()
        data = self._data([{"id": "D1", "text": "  ", "quantity": {}}])
        assert rule.validate({"data": data}) is False

    def test_empty_fails(self):
        rule = RuleDDF00033()
        data = self._data([{"id": "D1"}])
        assert rule.validate({"data": data}) is False
