"""Tests for RuleDDF00009 — ScheduledTimeline anchor timing check."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00009 import RuleDDF00009
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00009:
    def test_metadata(self):
        rule = RuleDDF00009()
        assert rule._rule == "DDF00009"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, timelines):
        data = MagicMock()
        data.instances_by_klass.return_value = timelines
        data.path_by_id.return_value = "$.path"
        return data

    def test_timeline_with_fixed_reference_passes(self):
        rule = RuleDDF00009()
        data = self._data(
            [
                {
                    "id": "T1",
                    "instanceType": "ScheduledTimeline",
                    "timings": [
                        {"type": {"decode": "Before"}},
                        {"type": {"decode": "Fixed Reference"}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_timeline_without_fixed_reference_fails(self):
        rule = RuleDDF00009()
        data = self._data(
            [
                {
                    "id": "T1",
                    "instanceType": "ScheduledTimeline",
                    "timings": [
                        {"type": {"decode": "Before"}},
                        {"type": {"decode": "After"}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_empty_timings_fails(self):
        rule = RuleDDF00009()
        data = self._data(
            [{"id": "T1", "instanceType": "ScheduledTimeline", "timings": []}]
        )
        assert rule.validate({"data": data}) is False
