"""Tests for RuleDDF00197 — ISD.documentVersionIds uniqueness."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00197 import RuleDDF00197
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00197:
    def test_metadata(self):
        rule = RuleDDF00197()
        assert rule._rule == "DDF00197"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_unique_passes(self):
        rule = RuleDDF00197()
        data = self._data([{"id": "I1", "documentVersionIds": ["A", "B"]}])
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00197()
        data = self._data([{"id": "I1", "documentVersionIds": ["A", "A"]}])
        assert rule.validate({"data": data}) is False
