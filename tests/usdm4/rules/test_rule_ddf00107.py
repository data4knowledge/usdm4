"""Tests for RuleDDF00107 — SAI sub-timeline must belong to same StudyDesign."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00107 import RuleDDF00107
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00107:
    def test_metadata(self):
        rule = RuleDDF00107()
        assert rule._rule == "DDF00107"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "A scheduled activity instance must only have a sub-timeline that is defined within the same study design as the scheduled activity instance."
        )

    def _data(
        self,
        sais,
        instance_map=None,
        parent_map=None,
    ):
        data = MagicMock()
        data.instances_by_klass.return_value = sais
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda tid: (instance_map or {}).get(tid)
        data.parent_by_klass.side_effect = lambda tid, _klasses: (parent_map or {}).get(
            tid
        )
        return data

    def test_sai_without_timeline_id_is_skipped(self):
        rule = RuleDDF00107()
        data = self._data([{"id": "S1"}, {"id": "S2", "timelineId": None}])
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_unresolved_sub_timeline_is_skipped(self):
        """instance_by_id returns None → continue without failure."""
        rule = RuleDDF00107()
        data = self._data(
            [{"id": "S1", "timelineId": "ghost"}],
            instance_map={},
        )
        assert rule.validate({"data": data}) is True

    def test_missing_parent_design_is_skipped(self):
        """parent_by_klass returning None for either side → skip."""
        rule = RuleDDF00107()
        data = self._data(
            [{"id": "S1", "timelineId": "T1"}],
            instance_map={"T1": {"id": "T1"}},
            parent_map={"S1": None, "T1": None},
        )
        assert rule.validate({"data": data}) is True

    def test_mismatched_study_design_logs_failure(self):
        rule = RuleDDF00107()
        data = self._data(
            [{"id": "S1", "timelineId": "T1"}],
            instance_map={"T1": {"id": "T1"}},
            parent_map={"S1": {"id": "D1"}, "T1": {"id": "D2"}},
        )
        result = rule.validate({"data": data})
        assert result is False
        assert rule.errors().count() == 1

    def test_same_study_design_passes(self):
        rule = RuleDDF00107()
        data = self._data(
            [{"id": "S1", "timelineId": "T1"}],
            instance_map={"T1": {"id": "T1"}},
            parent_map={"S1": {"id": "D1"}, "T1": {"id": "D1"}},
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0
