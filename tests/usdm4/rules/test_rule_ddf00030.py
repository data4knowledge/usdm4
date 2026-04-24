"""Tests for RuleDDF00030 — PersonName.text required."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00030 import RuleDDF00030
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00030:
    def test_metadata(self):
        rule = RuleDDF00030()
        assert rule._rule == "DDF00030"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, persons):
        data = MagicMock()
        data.instances_by_klass.return_value = persons
        data.path_by_id.return_value = "$.path"
        return data

    def test_with_text_passes(self):
        rule = RuleDDF00030()
        data = self._data([{"id": "P1", "text": "Jane Doe"}])
        assert rule.validate({"data": data}) is True

    def test_empty_fails(self):
        rule = RuleDDF00030()
        data = self._data([{"id": "P1"}])
        assert rule.validate({"data": data}) is False
