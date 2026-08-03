"""Tests for RuleDDF00069 — StudyCell (arm,epoch) unique per scope."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00069 import RuleDDF00069
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00069:
    def test_metadata(self):
        rule = RuleDDF00069()
        assert rule._rule == "DDF00069"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, cells, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = cells
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda cid, _k: (parent_map or {}).get(cid)
        return data

    def test_no_scope_skipped(self):
        rule = RuleDDF00069()
        data = self._data(
            [{"id": "C1", "armId": "A1", "epochId": "E1"}], parent_map={"C1": None}
        )
        assert rule.validate({"data": data}) is True

    def test_unique_combinations_pass(self):
        rule = RuleDDF00069()
        data = self._data(
            [
                {"id": "C1", "armId": "A1", "epochId": "E1"},
                {"id": "C2", "armId": "A1", "epochId": "E2"},
                {"id": "C3", "armId": "A2", "epochId": "E1"},
            ],
            parent_map={"C1": {"id": "SD1"}, "C2": {"id": "SD1"}, "C3": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_same_pair_different_scope_passes(self):
        rule = RuleDDF00069()
        data = self._data(
            [
                {"id": "C1", "armId": "A1", "epochId": "E1"},
                {"id": "C2", "armId": "A1", "epochId": "E1"},
            ],
            parent_map={"C1": {"id": "SD1"}, "C2": {"id": "SD2"}},
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_pair_same_scope_fails(self):
        rule = RuleDDF00069()
        data = self._data(
            [
                {"id": "C1", "armId": "A1", "epochId": "E1"},
                {"id": "C2", "armId": "A1", "epochId": "E1"},
            ],
            parent_map={"C1": {"id": "SD1"}, "C2": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
