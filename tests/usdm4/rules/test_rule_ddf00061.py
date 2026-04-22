"""Tests for RuleDDF00061 — Timing.windowLower must be non-negative ISO 8601 duration."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00061 import RuleDDF00061
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00061:
    def test_metadata(self):
        rule = RuleDDF00061()
        assert rule._rule == "DDF00061"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, timings):
        data = MagicMock()
        data.instances_by_klass.return_value = timings
        data.path_by_id.return_value = "$.path"
        return data

    def test_empty_skipped(self):
        rule = RuleDDF00061()
        data = self._data([{"id": "T1"}, {"id": "T2", "windowLower": ""}])
        assert rule.validate({"data": data}) is True

    def test_valid_passes(self):
        rule = RuleDDF00061()
        data = self._data([{"id": "T1", "windowLower": "PT1H"}])
        assert rule.validate({"data": data}) is True

    def test_negative_fails(self):
        rule = RuleDDF00061()
        data = self._data([{"id": "T1", "windowLower": "-PT1H"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_invalid_format_fails(self):
        rule = RuleDDF00061()
        data = self._data([{"id": "T1", "windowLower": "abc"}])
        assert rule.validate({"data": data}) is False
