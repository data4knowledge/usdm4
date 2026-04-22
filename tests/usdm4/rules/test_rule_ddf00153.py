"""Tests for RuleDDF00153 — main ScheduleTimeline needs plannedDuration."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00153 import RuleDDF00153
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00153:
    def test_metadata(self):
        rule = RuleDDF00153()
        assert rule._rule == "DDF00153"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_main_skipped(self):
        rule = RuleDDF00153()
        data = self._data([{"id": "T1", "mainTimeline": False}])
        assert rule.validate({"data": data}) is True

    def test_main_with_duration_passes(self):
        rule = RuleDDF00153()
        data = self._data(
            [{"id": "T1", "mainTimeline": True, "plannedDuration": {"value": 30}}]
        )
        assert rule.validate({"data": data}) is True

    def test_main_without_duration_fails(self):
        rule = RuleDDF00153()
        data = self._data([{"id": "T1", "mainTimeline": True}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
