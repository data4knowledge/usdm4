"""Tests for RuleDDF00127 — Encounter.scheduledAtId same-StudyDesign."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00127 import RuleDDF00127
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00127:
    def test_metadata(self):
        rule = RuleDDF00127()
        assert rule._rule == "DDF00127"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, encounters, instance_map=None, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = encounters
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda tid: (instance_map or {}).get(tid)
        data.parent_by_klass.side_effect = lambda tid, _k: (parent_map or {}).get(tid)
        return data

    def test_no_timing_ref_skipped(self):
        rule = RuleDDF00127()
        data = self._data([{"id": "E1"}])
        assert rule.validate({"data": data}) is True

    def test_timing_not_found_skipped(self):
        rule = RuleDDF00127()
        data = self._data(
            [{"id": "E1", "scheduledAtId": "T1"}], instance_map={"T1": None}
        )
        assert rule.validate({"data": data}) is True

    def test_no_design_skipped(self):
        rule = RuleDDF00127()
        data = self._data(
            [{"id": "E1", "scheduledAtId": "T1"}],
            instance_map={"T1": {"id": "T1"}},
            parent_map={"E1": None, "T1": None},
        )
        assert rule.validate({"data": data}) is True

    def test_same_design_passes(self):
        rule = RuleDDF00127()
        data = self._data(
            [{"id": "E1", "scheduledAtId": "T1"}],
            instance_map={"T1": {"id": "T1"}},
            parent_map={"E1": {"id": "SD1"}, "T1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_cross_design_fails(self):
        rule = RuleDDF00127()
        data = self._data(
            [{"id": "E1", "scheduledAtId": "T1"}],
            instance_map={"T1": {"id": "T1"}},
            parent_map={"E1": {"id": "SD1"}, "T1": {"id": "SD2"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
