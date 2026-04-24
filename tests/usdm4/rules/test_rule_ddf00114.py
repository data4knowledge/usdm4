"""Tests for RuleDDF00114 — Condition.contextIds valid class."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00114 import RuleDDF00114
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00114:
    def test_metadata(self):
        rule = RuleDDF00114()
        assert rule._rule == "DDF00114"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, conditions, id_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = conditions
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda i: (id_map or {}).get(i)
        return data

    def test_empty_skipped(self):
        rule = RuleDDF00114()
        data = self._data([{"id": "C1"}, {"id": "C2", "contextIds": [""]}])
        assert rule.validate({"data": data}) is True

    def test_allowed_context_passes(self):
        rule = RuleDDF00114()
        data = self._data(
            [{"id": "C1", "contextIds": ["A1", "S1"]}],
            id_map={
                "A1": {"instanceType": "Activity"},
                "S1": {"instanceType": "ScheduledActivityInstance"},
            },
        )
        assert rule.validate({"data": data}) is True

    def test_unresolved_fails(self):
        rule = RuleDDF00114()
        data = self._data([{"id": "C1", "contextIds": ["ghost"]}])
        assert rule.validate({"data": data}) is False
        assert "does not resolve" in rule.errors().dump()

    def test_wrong_class_fails(self):
        rule = RuleDDF00114()
        data = self._data(
            [{"id": "C1", "contextIds": ["E1"]}],
            id_map={"E1": {"instanceType": "Encounter"}},
        )
        assert rule.validate({"data": data}) is False
        assert "resolves to Encounter" in rule.errors().dump()
