"""Tests for RuleDDF00034 — Duration.durationWillVary iff reasonDurationWillVary."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00034 import RuleDDF00034
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00034:
    def test_metadata(self):
        rule = RuleDDF00034()
        assert rule._rule == "DDF00034"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_both_set_passes(self):
        rule = RuleDDF00034()
        data = self._data(
            [{"id": "D1", "durationWillVary": True, "reasonDurationWillVary": "why"}]
        )
        assert rule.validate({"data": data}) is True

    def test_neither_set_passes(self):
        rule = RuleDDF00034()
        data = self._data([{"id": "D1"}])
        assert rule.validate({"data": data}) is True

    def test_flag_without_reason_fails(self):
        rule = RuleDDF00034()
        data = self._data([{"id": "D1", "durationWillVary": True}])
        assert rule.validate({"data": data}) is False
        assert "reasonDurationWillVary is missing" in rule.errors().dump()

    def test_reason_without_flag_fails(self):
        rule = RuleDDF00034()
        data = self._data([{"id": "D1", "reasonDurationWillVary": "why"}])
        assert rule.validate({"data": data}) is False
        assert "reasonDurationWillVary is set" in rule.errors().dump()
