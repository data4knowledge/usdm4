"""Tests for RuleDDF00060 — Timing.value must be non-negative ISO 8601 duration."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00060 import RuleDDF00060
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00060:
    def test_metadata(self):
        rule = RuleDDF00060()
        assert rule._rule == "DDF00060"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, timings):
        data = MagicMock()
        data.instances_by_klass.return_value = timings
        data.path_by_id.return_value = "$.path"
        return data

    def test_empty_value_skipped(self):
        rule = RuleDDF00060()
        data = self._data([{"id": "T1", "value": None}, {"id": "T2", "value": ""}])
        assert rule.validate({"data": data}) is True

    def test_valid_durations_pass(self):
        rule = RuleDDF00060()
        data = self._data(
            [
                {"id": "T1", "value": "P1D"},
                {"id": "T2", "value": "PT1H30M"},
                {"id": "T3", "value": "P1Y2M3DT4H5M6S"},
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_negative_duration_fails(self):
        rule = RuleDDF00060()
        data = self._data([{"id": "T1", "value": "-P1D"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_gibberish_fails(self):
        rule = RuleDDF00060()
        data = self._data([{"id": "T1", "value": "not a duration"}])
        assert rule.validate({"data": data}) is False
