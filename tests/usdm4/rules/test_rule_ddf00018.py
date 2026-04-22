"""Tests for RuleDDF00018 — no self-reference in childIds."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00018 import RuleDDF00018
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00018:
    def test_metadata(self):
        rule = RuleDDF00018()
        assert rule._rule == "DDF00018"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_children_passes(self):
        rule = RuleDDF00018()
        data = self._data({"Activity": [{"id": "A1"}]})
        assert rule.validate({"data": data}) is True

    def test_distinct_children_passes(self):
        rule = RuleDDF00018()
        data = self._data({"Activity": [{"id": "A1", "childIds": ["A2", "A3"]}]})
        assert rule.validate({"data": data}) is True

    def test_self_reference_fails(self):
        rule = RuleDDF00018()
        data = self._data({"Activity": [{"id": "A1", "childIds": ["A2", "A1"]}]})
        assert rule.validate({"data": data}) is False
        assert "references itself" in rule.errors().dump()

    def test_triggered_for_narrative(self):
        rule = RuleDDF00018()
        data = self._data({"NarrativeContent": [{"id": "N1", "childIds": ["N1"]}]})
        assert rule.validate({"data": data}) is False
