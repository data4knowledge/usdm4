"""Tests for RuleDDF00170 — Abbreviation.abbreviatedText unique per StudyVersion."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00170 import RuleDDF00170
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00170:
    def test_metadata(self):
        rule = RuleDDF00170()
        assert rule._rule == "DDF00170"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda i, _k: (parent_map or {}).get(i)
        return data

    def test_no_scope_skipped(self):
        rule = RuleDDF00170()
        data = self._data(
            [{"id": "A1", "abbreviatedText": "ABC"}], parent_map={"A1": None}
        )
        assert rule.validate({"data": data}) is True

    def test_unique_passes(self):
        rule = RuleDDF00170()
        data = self._data(
            [
                {"id": "A1", "abbreviatedText": "ABC"},
                {"id": "A2", "abbreviatedText": "DEF"},
            ],
            parent_map={"A1": {"id": "SV1"}, "A2": {"id": "SV1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_same_text_different_scope_passes(self):
        rule = RuleDDF00170()
        data = self._data(
            [
                {"id": "A1", "abbreviatedText": "ABC"},
                {"id": "A2", "abbreviatedText": "ABC"},
            ],
            parent_map={"A1": {"id": "SV1"}, "A2": {"id": "SV2"}},
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_same_scope_fails(self):
        rule = RuleDDF00170()
        data = self._data(
            [
                {"id": "A1", "abbreviatedText": "ABC"},
                {"id": "A2", "abbreviatedText": "ABC"},
            ],
            parent_map={"A1": {"id": "SV1"}, "A2": {"id": "SV1"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
