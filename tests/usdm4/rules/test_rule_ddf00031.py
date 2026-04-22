"""Tests for RuleDDF00031 — non-Fixed-Reference Timing must point to two distinct SIs."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00031 import RuleDDF00031
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00031:
    def test_metadata(self):
        rule = RuleDDF00031()
        assert rule._rule == "DDF00031"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, timings):
        data = MagicMock()
        data.instances_by_klass.return_value = timings
        data.path_by_id.return_value = "$.path"
        return data

    def test_fixed_reference_is_skipped(self):
        rule = RuleDDF00031()
        data = self._data([{"id": "T1", "type": {"decode": "Fixed Reference"}}])
        assert rule.validate({"data": data}) is True

    def test_missing_both_fails_twice(self):
        rule = RuleDDF00031()
        data = self._data([{"id": "T1", "type": {"decode": "Before"}}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2

    def test_missing_only_relative_to_fails_once(self):
        rule = RuleDDF00031()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"decode": "Before"},
                    "relativeFromScheduledInstanceId": "S1",
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_equal_ids_fails(self):
        rule = RuleDDF00031()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"decode": "Before"},
                    "relativeFromScheduledInstanceId": "S1",
                    "relativeToScheduledInstanceId": "S1",
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_distinct_ids_pass(self):
        rule = RuleDDF00031()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"decode": "Before"},
                    "relativeFromScheduledInstanceId": "S1",
                    "relativeToScheduledInstanceId": "S2",
                }
            ]
        )
        assert rule.validate({"data": data}) is True
