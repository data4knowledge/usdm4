"""Tests for RuleDDF00080 — main-timeline SAIs must refer to an epoch."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00080 import RuleDDF00080
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00080:
    def test_metadata(self):
        rule = RuleDDF00080()
        assert rule._rule == "DDF00080"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, sais, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = sais
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda i, _k: (parent_map or {}).get(i)
        return data

    def test_non_main_timeline_skipped(self):
        rule = RuleDDF00080()
        data = self._data(
            [{"id": "S1"}],
            parent_map={"S1": {"mainTimeline": False}},
        )
        assert rule.validate({"data": data}) is True

    def test_no_parent_timeline_skipped(self):
        rule = RuleDDF00080()
        data = self._data([{"id": "S1"}], parent_map={"S1": None})
        assert rule.validate({"data": data}) is True

    def test_main_with_epoch_passes(self):
        rule = RuleDDF00080()
        data = self._data(
            [{"id": "S1", "epochId": "E1"}],
            parent_map={"S1": {"mainTimeline": True}},
        )
        assert rule.validate({"data": data}) is True

    def test_main_without_epoch_fails(self):
        rule = RuleDDF00080()
        data = self._data(
            [{"id": "S1"}],
            parent_map={"S1": {"mainTimeline": True}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
