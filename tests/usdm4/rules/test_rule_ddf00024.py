"""Tests for RuleDDF00024 — StudyEpoch previousId/nextId same-StudyDesign check."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00024 import RuleDDF00024
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00024:
    def test_metadata(self):
        rule = RuleDDF00024()
        assert rule._rule == "DDF00024"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "An epoch must only reference epochs that are specified within the same study design."
        )

    def _data(self, epochs, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = epochs
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda eid, _k: (parent_map or {}).get(eid)
        return data

    def test_no_parent_for_epoch_skipped(self):
        rule = RuleDDF00024()
        data = self._data([{"id": "E1", "previousId": "E0"}], parent_map={})
        assert rule.validate({"data": data}) is True

    def test_missing_previous_and_next_skipped(self):
        rule = RuleDDF00024()
        data = self._data([{"id": "E1"}], parent_map={"E1": {"id": "SD1"}})
        assert rule.validate({"data": data}) is True

    def test_target_with_no_parent_skipped(self):
        rule = RuleDDF00024()
        data = self._data(
            [{"id": "E1", "nextId": "ORPHAN"}],
            parent_map={"E1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_same_design_passes(self):
        rule = RuleDDF00024()
        data = self._data(
            [{"id": "E1", "previousId": "E0", "nextId": "E2"}],
            parent_map={
                "E1": {"id": "SD1"},
                "E0": {"id": "SD1"},
                "E2": {"id": "SD1"},
            },
        )
        assert rule.validate({"data": data}) is True

    def test_different_design_fails(self):
        rule = RuleDDF00024()
        data = self._data(
            [{"id": "E1", "previousId": "E0", "nextId": "E2"}],
            parent_map={
                "E1": {"id": "SD1"},
                "E0": {"id": "SD2"},
                "E2": {"id": "SD3"},
            },
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
