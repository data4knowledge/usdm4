"""Tests for RuleDDF00007 — Fixed-Reference Timing relativeTo/From consistency."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00007 import RuleDDF00007
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00007:
    def test_metadata(self):
        rule = RuleDDF00007()
        assert rule._rule == "DDF00007"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, timings):
        data = MagicMock()
        data.instances_by_klass.return_value = timings
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_dict_type_skipped(self):
        rule = RuleDDF00007()
        data = self._data([{"id": "T1", "type": "bad"}])
        assert rule.validate({"data": data}) is True

    def test_non_fixed_reference_skipped(self):
        rule = RuleDDF00007()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"code": "OTHER"},
                    "relativeToScheduledInstanceId": "A",
                    "relativeFromScheduledInstanceId": "B",
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_absent_to_id_passes(self):
        rule = RuleDDF00007()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"code": "C201358"},
                    "relativeToScheduledInstanceId": None,
                    "relativeFromScheduledInstanceId": "A",
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_equal_ids_pass(self):
        rule = RuleDDF00007()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"code": "C201358"},
                    "relativeToScheduledInstanceId": "A",
                    "relativeFromScheduledInstanceId": "A",
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_mismatched_ids_fail(self):
        rule = RuleDDF00007()
        data = self._data(
            [
                {
                    "id": "T1",
                    "type": {"code": "C201358"},
                    "relativeToScheduledInstanceId": "A",
                    "relativeFromScheduledInstanceId": "B",
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
