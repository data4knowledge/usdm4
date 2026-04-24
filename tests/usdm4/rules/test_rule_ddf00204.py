"""Tests for RuleDDF00204 — NarrativeContent.next id refs."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00204 import RuleDDF00204
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00204:
    def test_metadata(self):
        rule = RuleDDF00204()
        assert rule._rule == "DDF00204"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "Narrative content must only reference narrative content that is specified within the same study definition document version."
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
        rule = RuleDDF00204()
        data = self._data([{"id": "N1", "next": None}])
        assert rule.validate({"data": data}) is True

    def test_resolved_passes(self):
        rule = RuleDDF00204()
        data = self._data([{"id": "N1", "next": "N2"}], resolvable={"N2"})
        assert rule.validate({"data": data}) is True

    def test_unresolved_fails(self):
        rule = RuleDDF00204()
        data = self._data([{"id": "N1", "next": "N2"}])
        assert rule.validate({"data": data}) is False
        assert "next references unresolved id 'N2'" in rule.errors().dump()
