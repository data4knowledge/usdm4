"""Tests for RuleDDF00028 — Activity previousId/nextId same-StudyDesign check."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00028 import RuleDDF00028
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00028:
    def test_metadata(self):
        rule = RuleDDF00028()
        assert rule._rule == "DDF00028"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "An activity must only reference activities that are specified within the same study design."
        )

    def _data(self, activities, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = activities
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda aid, _k: (parent_map or {}).get(aid)
        return data

    def test_no_parent_skipped(self):
        rule = RuleDDF00028()
        data = self._data([{"id": "A1", "previousId": "A0"}], parent_map={})
        assert rule.validate({"data": data}) is True

    def test_missing_refs_skipped(self):
        rule = RuleDDF00028()
        data = self._data([{"id": "A1"}], parent_map={"A1": {"id": "SD1"}})
        assert rule.validate({"data": data}) is True

    def test_unresolved_target_skipped(self):
        rule = RuleDDF00028()
        data = self._data(
            [{"id": "A1", "nextId": "X"}],
            parent_map={"A1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_same_design_passes(self):
        rule = RuleDDF00028()
        data = self._data(
            [{"id": "A1", "previousId": "A0", "nextId": "A2"}],
            parent_map={
                "A1": {"id": "SD1"},
                "A0": {"id": "SD1"},
                "A2": {"id": "SD1"},
            },
        )
        assert rule.validate({"data": data}) is True

    def test_cross_design_fails(self):
        rule = RuleDDF00028()
        data = self._data(
            [{"id": "A1", "previousId": "A0"}],
            parent_map={"A1": {"id": "SD1"}, "A0": {"id": "SD2"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
