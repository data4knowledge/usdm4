"""Tests for RuleDDF00247 — Syntax template text must be well-formed XHTML."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00247 import (
    RuleDDF00247,
    SCOPE_CLASSES,
    _is_well_formed,
)
from usdm4.rules.rule_template import RuleTemplate


def test_is_well_formed_true_for_simple():
    assert _is_well_formed("<p>hello</p>") is True


def test_is_well_formed_true_for_plain_text():
    assert _is_well_formed("plain text") is True


def test_is_well_formed_false_for_broken():
    assert _is_well_formed("<p>unclosed") is False


class TestRuleDDF00247:
    def test_metadata(self):
        rule = RuleDDF00247()
        assert rule._rule == "DDF00247"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_empty_and_non_string_skipped(self):
        rule = RuleDDF00247()
        data = self._data(
            {
                "Objective": [
                    {"id": "O1", "text": ""},
                    {"id": "O2", "text": "   "},
                    {"id": "O3", "text": None},
                    {"id": "O4"},
                ]
            }
        )
        assert rule.validate({"data": data}) is True

    def test_well_formed_passes(self):
        rule = RuleDDF00247()
        data = self._data({"Endpoint": [{"id": "E1", "text": "<p>Safe content</p>"}]})
        assert rule.validate({"data": data}) is True

    def test_malformed_fails(self):
        rule = RuleDDF00247()
        data = self._data({"Condition": [{"id": "C1", "text": "<p>unclosed"}]})
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_scope_classes_constant(self):
        assert "Objective" in SCOPE_CLASSES
        assert "Endpoint" in SCOPE_CLASSES
        assert len(SCOPE_CLASSES) == 6
