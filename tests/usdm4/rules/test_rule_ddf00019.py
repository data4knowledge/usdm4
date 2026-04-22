"""Tests for RuleDDF00019 — SAI/SDI defaultConditionId != self."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00019 import RuleDDF00019
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00019:
    def test_metadata(self):
        rule = RuleDDF00019()
        assert rule._rule == "DDF00019"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_distinct_passes(self):
        rule = RuleDDF00019()
        data = self._data(
            {"ScheduledActivityInstance": [{"id": "S1", "defaultConditionId": "X"}]}
        )
        assert rule.validate({"data": data}) is True

    def test_self_fails(self):
        rule = RuleDDF00019()
        data = self._data(
            {"ScheduledDecisionInstance": [{"id": "S1", "defaultConditionId": "S1"}]}
        )
        assert rule.validate({"data": data}) is False
        assert "refers to itself" in rule.errors().dump()
