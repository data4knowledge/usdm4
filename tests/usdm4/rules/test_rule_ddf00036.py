"""Tests for RuleDDF00036 — Fixed Reference => relativeToFrom 'Start to Start'."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00036 import RuleDDF00036
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00036:
    def test_metadata(self):
        rule = RuleDDF00036()
        assert rule._rule == "DDF00036"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_fixed_reference_skipped(self):
        rule = RuleDDF00036()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"decode": "After"},
                    "relativeToFrom": {"decode": "End to Start"},
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_fixed_reference_start_to_start_passes(self):
        rule = RuleDDF00036()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"decode": "Fixed Reference"},
                    "relativeToFrom": {"decode": "Start to Start"},
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_fixed_reference_wrong_relative_fails(self):
        rule = RuleDDF00036()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"decode": "Fixed Reference"},
                    "relativeToFrom": {"decode": "End to End"},
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
        assert "Invalid relativeToFrom" in rule.errors().dump()
