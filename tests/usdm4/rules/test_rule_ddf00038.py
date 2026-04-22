"""Tests for RuleDDF00038 — ScheduledDecisionInstance.defaultCondition id refs."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00038 import RuleDDF00038
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00038:
    def test_metadata(self):
        rule = RuleDDF00038()
        assert rule._rule == "DDF00038"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "A scheduled decision instance must refer to a default condition."
        )

    def _data(self, items, resolvable=None):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        resolvable = resolvable or set()
        data.instance_by_id.side_effect = lambda i: (
            {"id": i} if i in resolvable else None
        )
        return data

    def test_empty_values_skipped(self):
        rule = RuleDDF00038()
        data = self._data(
            [
                {"id": "S1", "defaultCondition": None},
                {"id": "S2", "defaultCondition": ""},
                {"id": "S3", "defaultCondition": []},
                {"id": "S4", "defaultCondition": {}},
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_resolved_passes(self):
        rule = RuleDDF00038()
        data = self._data([{"id": "S1", "defaultCondition": "D1"}], resolvable={"D1"})
        assert rule.validate({"data": data}) is True

    def test_unresolved_fails(self):
        rule = RuleDDF00038()
        data = self._data([{"id": "S1", "defaultCondition": "D1"}])
        assert rule.validate({"data": data}) is False
        assert "unresolved id 'D1'" in rule.errors().dump()
