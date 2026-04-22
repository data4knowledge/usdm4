"""Tests for RuleDDF00187 — NarrativeContentItem.text well-formed XHTML."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00187 import RuleDDF00187, _is_well_formed
from usdm4.rules.rule_template import RuleTemplate


def test_is_well_formed_accepts_plain_and_xhtml():
    assert _is_well_formed("<p>ok</p>") is True
    assert _is_well_formed("plain text") is True


def test_is_well_formed_rejects_broken():
    assert _is_well_formed("<p>unterminated") is False


class TestRuleDDF00187:
    def test_metadata(self):
        rule = RuleDDF00187()
        assert rule._rule == "DDF00187"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_empty_and_missing_skipped(self):
        rule = RuleDDF00187()
        data = self._data(
            [
                {"id": "N1", "text": ""},
                {"id": "N2", "text": "  "},
                {"id": "N3", "text": None},
                {"id": "N4"},
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_well_formed_passes(self):
        rule = RuleDDF00187()
        data = self._data([{"id": "N1", "text": "<p>Well-formed</p>"}])
        assert rule.validate({"data": data}) is True

    def test_malformed_fails(self):
        rule = RuleDDF00187()
        data = self._data([{"id": "N1", "text": "<p>oops"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
