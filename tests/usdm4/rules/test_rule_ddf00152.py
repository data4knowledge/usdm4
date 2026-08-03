"""Tests for RuleDDF00152 — Activity.timelineId same-StudyDesign."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00152 import RuleDDF00152
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00152:
    def test_metadata(self):
        rule = RuleDDF00152()
        assert rule._rule == "DDF00152"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, activities, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = activities
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda i, _k: (parent_map or {}).get(i)
        return data

    def test_no_timeline_skipped(self):
        rule = RuleDDF00152()
        data = self._data([{"id": "A1"}])
        assert rule.validate({"data": data}) is True

    def test_no_design_skipped(self):
        rule = RuleDDF00152()
        data = self._data(
            [{"id": "A1", "timelineId": "T1"}], parent_map={"A1": None, "T1": None}
        )
        assert rule.validate({"data": data}) is True

    def test_same_design_passes(self):
        rule = RuleDDF00152()
        data = self._data(
            [{"id": "A1", "timelineId": "T1"}],
            parent_map={"A1": {"id": "SD1"}, "T1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_cross_design_fails(self):
        rule = RuleDDF00152()
        data = self._data(
            [{"id": "A1", "timelineId": "T1"}],
            parent_map={"A1": {"id": "SD1"}, "T1": {"id": "SD2"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
