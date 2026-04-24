"""Tests for RuleDDF00039 — Duration.durationWillVary XOR quantity."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00039 import RuleDDF00039
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00039:
    def test_metadata(self):
        rule = RuleDDF00039()
        assert rule._rule == "DDF00039"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_will_vary_no_qty_passes(self):
        rule = RuleDDF00039()
        data = self._data([{"id": "D1", "durationWillVary": True}])
        assert rule.validate({"data": data}) is True

    def test_qty_no_will_vary_passes(self):
        rule = RuleDDF00039()
        data = self._data([{"id": "D1", "quantity": {"value": 5}}])
        assert rule.validate({"data": data}) is True

    def test_will_vary_with_qty_fails(self):
        rule = RuleDDF00039()
        data = self._data(
            [{"id": "D1", "durationWillVary": True, "quantity": {"value": 5}}]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_neither_fails(self):
        rule = RuleDDF00039()
        data = self._data([{"id": "D1"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
