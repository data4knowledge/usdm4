"""Tests for RuleDDF00072 — StudyCell.epoch references must resolve."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00072 import RuleDDF00072
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00072:
    def test_metadata(self):
        rule = RuleDDF00072()
        assert rule._rule == "DDF00072"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "A study cell must only reference an epoch that is defined within the same study design as the study cell."
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
        rule = RuleDDF00072()
        data = self._data([{"id": "C1", "epoch": []}])
        assert rule.validate({"data": data}) is True

    def test_resolved_passes(self):
        rule = RuleDDF00072()
        data = self._data([{"id": "C1", "epoch": "E1"}], resolvable={"E1"})
        assert rule.validate({"data": data}) is True

    def test_unresolved_fails(self):
        rule = RuleDDF00072()
        data = self._data([{"id": "C1", "epoch": "E1"}])
        assert rule.validate({"data": data}) is False
        assert "epoch references unresolved id 'E1'" in rule.errors().dump()
