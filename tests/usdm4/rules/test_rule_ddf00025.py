"""Tests for RuleDDF00025 — no window on anchor (Fixed Reference) Timing."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00025 import RuleDDF00025
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00025:
    def test_metadata(self):
        rule = RuleDDF00025()
        assert rule._rule == "DDF00025"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, timings):
        data = MagicMock()
        data.instances_by_klass.return_value = timings
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_anchor_skipped(self):
        rule = RuleDDF00025()
        data = self._data(
            [{"id": "T1", "type": {"decode": "Before"}, "windowLower": "PT1H"}]
        )
        assert rule.validate({"data": data}) is True

    def test_anchor_no_window_passes(self):
        rule = RuleDDF00025()
        data = self._data([{"id": "T1", "type": {"decode": "Fixed Reference"}}])
        assert rule.validate({"data": data}) is True

    def test_anchor_window_none_passes(self):
        rule = RuleDDF00025()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"decode": "Fixed Reference"},
                    "windowLower": None,
                    "windowUpper": None,
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_anchor_with_window_lower_fails(self):
        rule = RuleDDF00025()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"decode": "Fixed Reference"},
                    "windowLower": "PT1H",
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_anchor_with_both_windows_fails(self):
        rule = RuleDDF00025()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"decode": "Fixed Reference"},
                    "windowLower": "PT1H",
                    "windowUpper": "PT2H",
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
