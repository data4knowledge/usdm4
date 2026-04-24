"""Tests for RuleDDF00011 — Fixed Reference Timing must have relativeFromScheduledInstance."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00011 import RuleDDF00011
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00011:
    def test_metadata(self):
        rule = RuleDDF00011()
        assert rule._rule == "DDF00011"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_fixed_skipped(self):
        rule = RuleDDF00011()
        data = self._data([{"id": "T1", "type": {"decode": "After"}}])
        assert rule.validate({"data": data}) is True

    def test_fixed_with_relative_passes(self):
        rule = RuleDDF00011()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"decode": "Fixed Reference"},
                    "relativeFromScheduledInstanceId": "SAI1",
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_fixed_missing_fails(self):
        rule = RuleDDF00011()
        data = self._data([{"id": "T1", "type": {"decode": "Fixed Reference"}}])
        assert rule.validate({"data": data}) is False
        assert "Missing relativeFromScheduledInstance" in rule.errors().dump()
