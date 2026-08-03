"""Tests for RuleDDF00062 — Timing.windowUpper must be non-negative ISO 8601 duration."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00062 import RuleDDF00062
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00062:
    def test_metadata(self):
        rule = RuleDDF00062()
        assert rule._rule == "DDF00062"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, timings):
        data = MagicMock()
        data.instances_by_klass.return_value = timings
        data.path_by_id.return_value = "$.path"
        return data

    def test_empty_skipped(self):
        rule = RuleDDF00062()
        data = self._data([{"id": "T1"}])
        assert rule.validate({"data": data}) is True

    def test_valid_passes(self):
        rule = RuleDDF00062()
        data = self._data([{"id": "T1", "windowUpper": "PT30M"}])
        assert rule.validate({"data": data}) is True

    def test_negative_fails(self):
        rule = RuleDDF00062()
        data = self._data([{"id": "T1", "windowUpper": "-PT30M"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_invalid_format_fails(self):
        rule = RuleDDF00062()
        data = self._data([{"id": "T1", "windowUpper": "xyz"}])
        assert rule.validate({"data": data}) is False
