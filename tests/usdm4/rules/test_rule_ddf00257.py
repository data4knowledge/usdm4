"""Tests for RuleDDF00257 — no Single Country + Multiple Countries together."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00257 import RuleDDF00257
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00257:
    def test_metadata(self):
        rule = RuleDDF00257()
        assert rule._rule == "DDF00257"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_only_single_passes(self):
        rule = RuleDDF00257()
        data = self._data([{"id": "D1", "characteristics": [{"code": "C217006"}]}])
        assert rule.validate({"data": data}) is True

    def test_both_fails(self):
        rule = RuleDDF00257()
        data = self._data(
            [
                {
                    "id": "D1",
                    "characteristics": [{"code": "C217006"}, {"code": "C217007"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "Incompatible codes" in rule.errors().dump()
