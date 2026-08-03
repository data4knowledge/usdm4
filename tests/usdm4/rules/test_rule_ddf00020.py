"""Tests for RuleDDF00020 — StudyAmendmentReason Other-code iff reason-text present."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00020 import RuleDDF00020
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00020:
    def test_metadata(self):
        rule = RuleDDF00020()
        assert rule._rule == "DDF00020"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_both_set_passes(self):
        rule = RuleDDF00020()
        data = self._data(
            [{"id": "R1", "code": {"code": "C17649"}, "otherReason": "reason"}]
        )
        assert rule.validate({"data": data}) is True

    def test_neither_set_passes(self):
        rule = RuleDDF00020()
        data = self._data([{"id": "R1", "code": {"code": "OTHER"}}])
        assert rule.validate({"data": data}) is True

    def test_code_but_no_reason_fails(self):
        rule = RuleDDF00020()
        data = self._data([{"id": "R1", "code": {"code": "C17649"}}])
        assert rule.validate({"data": data}) is False
        assert "otherReason is missing" in rule.errors().dump()

    def test_reason_but_no_code_fails(self):
        rule = RuleDDF00020()
        data = self._data(
            [{"id": "R1", "code": {"code": "OTHER"}, "otherReason": "reason"}]
        )
        assert rule.validate({"data": data}) is False
        assert "otherReason is set but code is missing" in rule.errors().dump()
