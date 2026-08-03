"""Tests for RuleDDF00071 — StudyCell.arm references must resolve."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00071 import RuleDDF00071
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00071:
    def test_metadata(self):
        rule = RuleDDF00071()
        assert rule._rule == "DDF00071"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "A study cell must only reference an arm that is defined within the same study design as the study cell."
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
        rule = RuleDDF00071()
        data = self._data([{"id": "C1", "arm": None}])
        assert rule.validate({"data": data}) is True

    def test_resolved_passes(self):
        rule = RuleDDF00071()
        data = self._data([{"id": "C1", "arm": "A1"}], resolvable={"A1"})
        assert rule.validate({"data": data}) is True

    def test_unresolved_fails(self):
        rule = RuleDDF00071()
        data = self._data([{"id": "C1", "arm": ["A1", "A2"]}], resolvable={"A1"})
        assert rule.validate({"data": data}) is False
        assert "arm references unresolved id 'A2'" in rule.errors().dump()
