"""Tests for RuleDDF00163 — NarrativeContent needs childIds or contentItemId."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00163 import RuleDDF00163
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00163:
    def test_metadata(self):
        rule = RuleDDF00163()
        assert rule._rule == "DDF00163"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_with_child_passes(self):
        rule = RuleDDF00163()
        data = self._data([{"id": "N1", "childIds": ["X"]}])
        assert rule.validate({"data": data}) is True

    def test_with_content_item_passes(self):
        rule = RuleDDF00163()
        data = self._data([{"id": "N1", "contentItemId": "C1"}])
        assert rule.validate({"data": data}) is True

    def test_neither_fails(self):
        rule = RuleDDF00163()
        data = self._data([{"id": "N1"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
