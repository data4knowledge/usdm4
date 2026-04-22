"""Tests for RuleDDF00174 — at most one StudyIdentifier per scopeId (warning)."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00174 import RuleDDF00174
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00174:
    def test_metadata(self):
        rule = RuleDDF00174()
        assert rule._rule == "DDF00174"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, identifiers):
        data = MagicMock()
        data.instances_by_klass.return_value = identifiers
        data.path_by_id.return_value = "$.path"
        return data

    def test_missing_scope_skipped(self):
        rule = RuleDDF00174()
        data = self._data([{"id": "I1"}])
        assert rule.validate({"data": data}) is True

    def test_single_scope_passes(self):
        rule = RuleDDF00174()
        data = self._data([{"id": "I1", "scopeId": "O1"}])
        assert rule.validate({"data": data}) is True

    def test_different_scopes_pass(self):
        rule = RuleDDF00174()
        data = self._data(
            [{"id": "I1", "scopeId": "O1"}, {"id": "I2", "scopeId": "O2"}]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_scope_fails(self):
        rule = RuleDDF00174()
        data = self._data(
            [{"id": "I1", "scopeId": "O1"}, {"id": "I2", "scopeId": "O1"}]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
