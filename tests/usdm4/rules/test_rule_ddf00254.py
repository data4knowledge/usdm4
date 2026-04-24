"""Tests for RuleDDF00254 — Activity.childIds same-StudyDesign check."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00254 import RuleDDF00254
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00254:
    def test_metadata(self):
        rule = RuleDDF00254()
        assert rule._rule == "DDF00254"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, activities, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = activities
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda aid, _k: (parent_map or {}).get(aid)
        return data

    def test_no_scope_skipped(self):
        rule = RuleDDF00254()
        data = self._data([{"id": "A1", "childIds": ["A2"]}], parent_map={"A1": None})
        assert rule.validate({"data": data}) is True

    def test_child_same_scope_passes(self):
        rule = RuleDDF00254()
        data = self._data(
            [
                {"id": "A1", "childIds": ["A2"]},
                {"id": "A2"},
            ],
            parent_map={"A1": {"id": "SD1"}, "A2": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_child_different_scope_fails(self):
        rule = RuleDDF00254()
        data = self._data(
            [
                {"id": "A1", "childIds": ["A2"]},
                {"id": "A2"},
            ],
            parent_map={"A1": {"id": "SD1"}, "A2": {"id": "SD2"}},
        )
        assert rule.validate({"data": data}) is False
        assert "outside the same scope" in rule.errors().dump()

    def test_child_missing_fails(self):
        rule = RuleDDF00254()
        data = self._data(
            [{"id": "A1", "childIds": ["UNKNOWN"]}],
            parent_map={"A1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is False
