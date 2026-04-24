"""Tests for RuleDDF00249 — EligibilityCriterion.criterionItem populated."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00249 import RuleDDF00249
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00249:
    def test_metadata(self):
        rule = RuleDDF00249()
        assert rule._rule == "DDF00249"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_populated_passes(self):
        rule = RuleDDF00249()
        data = self._data([{"id": "EC1", "criterionItem": {"id": "I1"}}])
        assert rule.validate({"data": data}) is True

    def test_empty_fails(self):
        rule = RuleDDF00249()
        data = self._data([{"id": "EC1"}])
        assert rule.validate({"data": data}) is False
