"""Tests for RuleDDF00184 — Substance.referenceSubstanceId not self."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00184 import RuleDDF00184
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00184:
    def test_metadata(self):
        rule = RuleDDF00184()
        assert rule._rule == "DDF00184"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_different_ref_passes(self):
        rule = RuleDDF00184()
        data = self._data([{"id": "S1", "referenceSubstanceId": "S2"}])
        assert rule.validate({"data": data}) is True

    def test_no_ref_passes(self):
        rule = RuleDDF00184()
        data = self._data([{"id": "S1"}])
        assert rule.validate({"data": data}) is True

    def test_self_ref_fails(self):
        rule = RuleDDF00184()
        data = self._data([{"id": "S1", "referenceSubstanceId": "S1"}])
        assert rule.validate({"data": data}) is False
        assert "refers to itself" in rule.errors().dump()
