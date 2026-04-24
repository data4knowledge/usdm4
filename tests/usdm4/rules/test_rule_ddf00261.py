"""Tests for RuleDDF00261 — GeographicScope: global type iff no code, non-global iff code."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00261 import RuleDDF00261
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00261:
    def test_metadata(self):
        rule = RuleDDF00261()
        assert rule._rule == "DDF00261"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_global_without_code_passes(self):
        rule = RuleDDF00261()
        data = self._data([{"id": "G1", "type": {"code": "C68846"}}])
        assert rule.validate({"data": data}) is True

    def test_non_global_with_code_passes(self):
        rule = RuleDDF00261()
        data = self._data(
            [{"id": "G1", "type": {"code": "OTHER"}, "code": {"code": "X"}}]
        )
        assert rule.validate({"data": data}) is True

    def test_global_with_code_fails(self):
        rule = RuleDDF00261()
        data = self._data(
            [
                {
                    "id": "G1",
                    "type": {"code": "C68846"},
                    "code": {"code": "X"},
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_non_global_without_code_fails(self):
        rule = RuleDDF00261()
        data = self._data([{"id": "G1", "type": {"code": "OTHER"}}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
