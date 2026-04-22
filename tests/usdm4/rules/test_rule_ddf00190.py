"""Tests for RuleDDF00190 — StudyRole persons XOR organizations."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00190 import RuleDDF00190
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00190:
    def test_metadata(self):
        rule = RuleDDF00190()
        assert rule._rule == "DDF00190"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_only_persons_passes(self):
        rule = RuleDDF00190()
        data = self._data([{"id": "R1", "assignedPersons": ["P1"]}])
        assert rule.validate({"data": data}) is True

    def test_only_orgs_passes(self):
        rule = RuleDDF00190()
        data = self._data([{"id": "R1", "organizationIds": ["O1"]}])
        assert rule.validate({"data": data}) is True

    def test_both_fails(self):
        rule = RuleDDF00190()
        data = self._data(
            [{"id": "R1", "assignedPersons": ["P1"], "organizationIds": ["O1"]}]
        )
        assert rule.validate({"data": data}) is False
        assert "both assignedPersons" in rule.errors().dump()
