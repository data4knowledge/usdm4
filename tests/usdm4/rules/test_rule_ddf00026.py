"""Tests for RuleDDF00026 — SAI.timelineId must not equal its own parent timeline."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00026 import RuleDDF00026
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00026:
    def test_metadata(self):
        rule = RuleDDF00026()
        assert rule._rule == "DDF00026"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, sais, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = sais
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda tid, _k: (parent_map or {}).get(tid)
        return data

    def test_no_timeline_id_skipped(self):
        rule = RuleDDF00026()
        data = self._data([{"id": "SAI1"}])
        assert rule.validate({"data": data}) is True

    def test_no_parent_timeline_skipped(self):
        rule = RuleDDF00026()
        data = self._data([{"id": "SAI1", "timelineId": "T2"}])
        assert rule.validate({"data": data}) is True

    def test_sub_timeline_matches_parent_fails(self):
        rule = RuleDDF00026()
        data = self._data(
            [{"id": "SAI1", "timelineId": "T1"}],
            parent_map={"SAI1": {"id": "T1"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_sub_timeline_differs_from_parent_passes(self):
        rule = RuleDDF00026()
        data = self._data(
            [{"id": "SAI1", "timelineId": "T2"}],
            parent_map={"SAI1": {"id": "T1"}},
        )
        assert rule.validate({"data": data}) is True
