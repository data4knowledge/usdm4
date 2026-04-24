"""Tests for RuleDDF00046 — Timing targets must live in the same ScheduleTimeline."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00046 import RuleDDF00046
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00046:
    def test_metadata(self):
        rule = RuleDDF00046()
        assert rule._rule == "DDF00046"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, timings, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = timings
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda tid, _k: (parent_map or {}).get(tid)
        return data

    def test_timing_without_parent_skipped(self):
        rule = RuleDDF00046()
        data = self._data([{"id": "T1"}])
        assert rule.validate({"data": data}) is True

    def test_target_without_parent_skipped(self):
        rule = RuleDDF00046()
        data = self._data(
            [{"id": "T1", "relativeFromScheduledInstanceId": "S1"}],
            parent_map={"T1": {"id": "TL1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_missing_target_id_skipped(self):
        rule = RuleDDF00046()
        data = self._data(
            [{"id": "T1", "relativeFromScheduledInstanceId": None}],
            parent_map={"T1": {"id": "TL1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_same_timeline_passes(self):
        rule = RuleDDF00046()
        data = self._data(
            [{"id": "T1", "relativeFromScheduledInstanceId": "S1"}],
            parent_map={"T1": {"id": "TL1"}, "S1": {"id": "TL1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_different_timeline_fails(self):
        rule = RuleDDF00046()
        data = self._data(
            [
                {
                    "id": "T1",
                    "relativeFromScheduledInstanceId": "S1",
                    "relativeToScheduledInstanceId": "S2",
                }
            ],
            parent_map={
                "T1": {"id": "TL1"},
                "S1": {"id": "TL2"},
                "S2": {"id": "TL1"},
            },
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
