"""Tests for RuleDDF00236 — BC synonym != label (case-insensitive)."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00236 import RuleDDF00236
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00236:
    def test_metadata(self):
        rule = RuleDDF00236()
        assert rule._rule == "DDF00236"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, bcs):
        data = MagicMock()
        data.instances_by_klass.return_value = bcs
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_label_skipped(self):
        rule = RuleDDF00236()
        data = self._data([{"id": "B1", "synonyms": ["x"]}])
        assert rule.validate({"data": data}) is True

    def test_distinct_passes(self):
        rule = RuleDDF00236()
        data = self._data([{"id": "B1", "label": "Weight", "synonyms": ["mass", "kg"]}])
        assert rule.validate({"data": data}) is True

    def test_case_insensitive_match_fails(self):
        rule = RuleDDF00236()
        data = self._data(
            [{"id": "B1", "label": "Weight", "synonyms": ["x", "WEIGHT"]}]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_non_string_synonym_ignored(self):
        rule = RuleDDF00236()
        data = self._data([{"id": "B1", "label": "Weight", "synonyms": [None, 123]}])
        assert rule.validate({"data": data}) is True
