"""Tests for RuleDDF00255 — StudyAmendment primaryReason != 'Not Applicable'."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00255 import RuleDDF00255
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00255:
    def test_metadata(self):
        rule = RuleDDF00255()
        assert rule._rule == "DDF00255"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, amendments):
        data = MagicMock()
        data.instances_by_klass.return_value = amendments
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_primary_skipped(self):
        rule = RuleDDF00255()
        data = self._data([{"id": "A1"}])
        assert rule.validate({"data": data}) is True

    def test_non_dict_primary_skipped(self):
        rule = RuleDDF00255()
        data = self._data([{"id": "A1", "primaryReason": "bad"}])
        assert rule.validate({"data": data}) is True

    def test_non_dict_code_skipped(self):
        rule = RuleDDF00255()
        data = self._data([{"id": "A1", "primaryReason": {"id": "P1", "code": "bad"}}])
        assert rule.validate({"data": data}) is True

    def test_applicable_passes(self):
        rule = RuleDDF00255()
        data = self._data(
            [{"id": "A1", "primaryReason": {"id": "P1", "code": {"code": "OTHER"}}}]
        )
        assert rule.validate({"data": data}) is True

    def test_not_applicable_fails(self):
        rule = RuleDDF00255()
        data = self._data(
            [{"id": "A1", "primaryReason": {"id": "P1", "code": {"code": "C48660"}}}]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
