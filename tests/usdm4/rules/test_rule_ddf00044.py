"""Tests for RuleDDF00044 — ConditionAssignment.conditionTargetId != parent id."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00044 import RuleDDF00044
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00044:
    def test_metadata(self):
        rule = RuleDDF00044()
        assert rule._rule == "DDF00044"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "The target for a condition must not be equal to its parent."
        )

    def _data(self, assignments, parent_dict=None):
        data = MagicMock()
        data.instances_by_klass.return_value = assignments
        data.path_by_id.return_value = "$.path"
        data._parent = parent_dict or {}
        return data

    def test_missing_target_skipped(self):
        rule = RuleDDF00044()
        data = self._data([{"id": "C1"}])
        assert rule.validate({"data": data}) is True

    def test_no_parent_skipped(self):
        rule = RuleDDF00044()
        data = self._data([{"id": "C1", "conditionTargetId": "X"}])
        assert rule.validate({"data": data}) is True

    def test_target_differs_from_parent_passes(self):
        rule = RuleDDF00044()
        data = self._data(
            [{"id": "C1", "conditionTargetId": "OTHER"}],
            parent_dict={"C1": {"id": "PARENT"}},
        )
        assert rule.validate({"data": data}) is True

    def test_target_equals_parent_fails(self):
        rule = RuleDDF00044()
        data = self._data(
            [{"id": "C1", "conditionTargetId": "PARENT"}],
            parent_dict={"C1": {"id": "PARENT"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
