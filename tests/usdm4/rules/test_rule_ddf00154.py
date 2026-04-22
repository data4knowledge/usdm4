"""Tests for RuleDDF00154 — no Single-Centre+Multicentre together."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00154 import RuleDDF00154
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00154:
    def test_metadata(self):
        rule = RuleDDF00154()
        assert rule._rule == "DDF00154"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_only_single_passes(self):
        rule = RuleDDF00154()
        data = self._data([{"id": "D1", "characteristics": [{"code": "C217004"}]}])
        assert rule.validate({"data": data}) is True

    def test_only_multi_passes(self):
        rule = RuleDDF00154()
        data = self._data([{"id": "D1", "characteristics": [{"code": "C217005"}]}])
        assert rule.validate({"data": data}) is True

    def test_both_fails(self):
        rule = RuleDDF00154()
        data = self._data(
            [
                {
                    "id": "D1",
                    "characteristics": [{"code": "C217004"}, {"code": "C217005"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "Incompatible codes" in rule.errors().dump()
