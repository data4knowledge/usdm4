"""Tests for RuleDDF00168 — NarrativeContent.contentItem id refs."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00168 import RuleDDF00168
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00168:
    def test_metadata(self):
        rule = RuleDDF00168()
        assert rule._rule == "DDF00168"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "A piece of narrative content must only reference narrative content items that have been defined within the study version as the narrative content."
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

    def test_empty_skipped(self):
        rule = RuleDDF00168()
        data = self._data([{"id": "N1", "contentItem": {}}])
        assert rule.validate({"data": data}) is True

    def test_resolved_passes(self):
        rule = RuleDDF00168()
        data = self._data(
            [{"id": "N1", "contentItem": ["I1", "I2"]}], resolvable={"I1", "I2"}
        )
        assert rule.validate({"data": data}) is True

    def test_unresolved_fails(self):
        rule = RuleDDF00168()
        data = self._data([{"id": "N1", "contentItem": "I1"}])
        assert rule.validate({"data": data}) is False
        assert "contentItem references unresolved id 'I1'" in rule.errors().dump()
