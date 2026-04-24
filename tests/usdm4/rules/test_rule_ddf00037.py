"""Tests for RuleDDF00037 — timeline must have >=1 SAI with timelineExit."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00037 import RuleDDF00037
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00037:
    def test_metadata(self):
        rule = RuleDDF00037()
        assert rule._rule == "DDF00037"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, timelines, sais, sai_parent_map=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "ScheduleTimeline": timelines,
            "ScheduledActivityInstance": sais,
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda sid, _k: (sai_parent_map or {}).get(
            sid
        )
        return data

    def test_no_sais_skipped(self):
        rule = RuleDDF00037()
        data = self._data([{"id": "TL1"}], [])
        assert rule.validate({"data": data}) is True

    def test_timeline_has_exit_passes(self):
        rule = RuleDDF00037()
        data = self._data(
            [{"id": "TL1"}],
            [{"id": "S1", "timelineExitId": "X"}],
            sai_parent_map={"S1": {"id": "TL1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_timeline_without_exit_fails(self):
        rule = RuleDDF00037()
        data = self._data(
            [{"id": "TL1"}],
            [{"id": "S1"}, {"id": "S2"}],
            sai_parent_map={"S1": {"id": "TL1"}, "S2": {"id": "TL1"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_sais_on_other_timeline_ignored(self):
        rule = RuleDDF00037()
        data = self._data(
            [{"id": "TL1"}],
            [{"id": "S1", "timelineExitId": "X"}],
            sai_parent_map={"S1": {"id": "OTHER"}},
        )
        # TL1 has no SAIs (all are on OTHER), so skipped
        assert rule.validate({"data": data}) is True
