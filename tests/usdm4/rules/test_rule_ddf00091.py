"""Tests for RuleDDF00091 — Condition.appliesToIds resolve to allowed class."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00091 import RuleDDF00091
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00091:
    def test_metadata(self):
        rule = RuleDDF00091()
        assert rule._rule == "DDF00091"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, conditions, id_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = conditions
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda i: (id_map or {}).get(i)
        return data

    def test_empty_ids_skipped(self):
        rule = RuleDDF00091()
        data = self._data([{"id": "C1"}, {"id": "C2", "appliesToIds": [""]}])
        assert rule.validate({"data": data}) is True

    def test_allowed_targets_pass(self):
        rule = RuleDDF00091()
        data = self._data(
            [{"id": "C1", "appliesToIds": ["P1", "A1"]}],
            id_map={
                "P1": {"instanceType": "Procedure"},
                "A1": {"instanceType": "Activity"},
            },
        )
        assert rule.validate({"data": data}) is True

    def test_unresolved_fails(self):
        rule = RuleDDF00091()
        data = self._data([{"id": "C1", "appliesToIds": ["ghost"]}], id_map={})
        assert rule.validate({"data": data}) is False
        assert "does not resolve" in rule.errors().dump()

    def test_wrong_type_fails(self):
        rule = RuleDDF00091()
        data = self._data(
            [{"id": "C1", "appliesToIds": ["X1"]}],
            id_map={"X1": {"instanceType": "Encounter"}},
        )
        assert rule.validate({"data": data}) is False
        assert "resolves to Encounter" in rule.errors().dump()
