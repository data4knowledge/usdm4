"""Tests for RuleDDF00256 — primary and secondary reason codes must differ."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00256 import RuleDDF00256
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00256:
    def test_metadata(self):
        rule = RuleDDF00256()
        assert rule._rule == "DDF00256"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, amendments):
        data = MagicMock()
        data.instances_by_klass.return_value = amendments
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_primary_skipped(self):
        rule = RuleDDF00256()
        data = self._data([{"id": "A1"}])
        assert rule.validate({"data": data}) is True

    def test_primary_non_dict_skipped(self):
        rule = RuleDDF00256()
        data = self._data([{"id": "A1", "primaryReason": "bad"}])
        assert rule.validate({"data": data}) is True

    def test_primary_no_code_skipped(self):
        rule = RuleDDF00256()
        data = self._data([{"id": "A1", "primaryReason": {"code": None}}])
        assert rule.validate({"data": data}) is True

    def test_distinct_codes_pass(self):
        rule = RuleDDF00256()
        data = self._data(
            [
                {
                    "id": "A1",
                    "primaryReason": {"code": {"code": "X"}},
                    "secondaryReasons": [{"id": "S1", "code": {"code": "Y"}}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_code_fails(self):
        rule = RuleDDF00256()
        data = self._data(
            [
                {
                    "id": "A1",
                    "primaryReason": {"code": {"code": "X"}},
                    "secondaryReasons": [{"id": "S1", "code": {"code": "X"}}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
