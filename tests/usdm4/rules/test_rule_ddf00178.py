"""Tests for RuleDDF00178 — Administration.dose implies frequency."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00178 import RuleDDF00178
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00178:
    def test_metadata(self):
        rule = RuleDDF00178()
        assert rule._rule == "DDF00178"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_dose_passes(self):
        rule = RuleDDF00178()
        data = self._data([{"id": "A1"}])
        assert rule.validate({"data": data}) is True

    def test_dose_with_frequency_passes(self):
        rule = RuleDDF00178()
        data = self._data(
            [{"id": "A1", "dose": {"value": 10}, "frequency": {"code": "D"}}]
        )
        assert rule.validate({"data": data}) is True

    def test_dose_without_frequency_fails(self):
        rule = RuleDDF00178()
        data = self._data([{"id": "A1", "dose": {"value": 10}}])
        assert rule.validate({"data": data}) is False
        assert "frequency is missing" in rule.errors().dump()
