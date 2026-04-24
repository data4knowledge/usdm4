"""Tests for RuleDDF00022 — nextId must not be self."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00022 import RuleDDF00022
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00022:
    def test_metadata(self):
        rule = RuleDDF00022()
        assert rule._rule == "DDF00022"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_distinct_passes(self):
        rule = RuleDDF00022()
        data = self._data({"Encounter": [{"id": "E1", "nextId": "E2"}]})
        assert rule.validate({"data": data}) is True

    def test_self_next_fails(self):
        rule = RuleDDF00022()
        data = self._data({"Activity": [{"id": "A1", "nextId": "A1"}]})
        assert rule.validate({"data": data}) is False
        assert "refers to itself" in rule.errors().dump()
