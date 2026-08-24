"""Tests for RuleDDF00031 — non-Fixed-Reference Timing must point to two distinct SIs."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00031 import RuleDDF00031
from usdm4.rules.rule_template import RuleTemplate

FIXED = {"code": "C201358", "decode": "Fixed Reference Timing Type"}
BEFORE = {"code": "C201357", "decode": "Before Timing Type"}


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
        data = self._data([{"id": "T1", "type": FIXED}])
        assert rule.validate({"data": data}) is True

    def test_fixed_reference_self_referencing_is_skipped(self):
        """Regression: an anchor timing points at itself by design. Before the
        fix the decode comparison never matched, so every anchor in the corpus
        was reported as a failure."""
        rule = RuleDDF00031()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": FIXED,
                    "relativeFromScheduledInstanceId": "S1",
                    "relativeToScheduledInstanceId": "S1",
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_missing_both_fails_twice(self):
        rule = RuleDDF00031()
        data = self._data([{"id": "T1", "type": BEFORE}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2

    def test_missing_only_relative_to_fails_once(self):
        rule = RuleDDF00031()
        data = self._data(
            [{"id": "T1", "type": BEFORE, "relativeFromScheduledInstanceId": "S1"}]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_equal_ids_fails(self):
        rule = RuleDDF00031()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": BEFORE,
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
                    "type": BEFORE,
                    "relativeFromScheduledInstanceId": "S1",
                    "relativeToScheduledInstanceId": "S2",
                }
            ]
        )
        assert rule.validate({"data": data}) is True
