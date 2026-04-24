"""Tests for RuleDDF00173 — identifier (klass, scopeId, text) uniqueness."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00173 import RuleDDF00173
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00173:
    def test_metadata(self):
        rule = RuleDDF00173()
        assert rule._rule == "DDF00173"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_missing_fields_skipped(self):
        rule = RuleDDF00173()
        data = self._data(
            {"StudyIdentifier": [{"id": "I1", "text": None, "scopeId": "O1"}]}
        )
        assert rule.validate({"data": data}) is True

    def test_unique_passes(self):
        rule = RuleDDF00173()
        data = self._data(
            {
                "StudyIdentifier": [
                    {"id": "I1", "text": "A", "scopeId": "O1"},
                    {"id": "I2", "text": "B", "scopeId": "O1"},
                ]
            }
        )
        assert rule.validate({"data": data}) is True

    def test_same_text_different_scope_passes(self):
        rule = RuleDDF00173()
        data = self._data(
            {
                "StudyIdentifier": [
                    {"id": "I1", "text": "A", "scopeId": "O1"},
                    {"id": "I2", "text": "A", "scopeId": "O2"},
                ]
            }
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00173()
        data = self._data(
            {
                "StudyIdentifier": [
                    {"id": "I1", "text": "A", "scopeId": "O1"},
                    {"id": "I2", "text": "A", "scopeId": "O1"},
                ]
            }
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
