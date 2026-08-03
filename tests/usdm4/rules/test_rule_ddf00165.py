"""Tests for RuleDDF00165 — NarrativeContent displaySectionTitle ↔ sectionTitle."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00165 import RuleDDF00165
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00165:
    def test_metadata(self):
        rule = RuleDDF00165()
        assert rule._rule == "DDF00165"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_both_set_passes(self):
        rule = RuleDDF00165()
        data = self._data(
            [{"id": "N1", "displaySectionTitle": True, "sectionTitle": "Intro"}]
        )
        assert rule.validate({"data": data}) is True

    def test_both_unset_passes(self):
        rule = RuleDDF00165()
        data = self._data([{"id": "N1"}])
        assert rule.validate({"data": data}) is True

    def test_display_without_title_fails(self):
        rule = RuleDDF00165()
        data = self._data(
            [{"id": "N1", "displaySectionTitle": True, "sectionTitle": ""}]
        )
        assert rule.validate({"data": data}) is False
        assert "sectionTitle is missing" in rule.errors().dump()

    def test_title_without_display_fails(self):
        rule = RuleDDF00165()
        data = self._data(
            [{"id": "N1", "displaySectionTitle": False, "sectionTitle": "Intro"}]
        )
        assert rule.validate({"data": data}) is False
        assert "displaySectionTitle is missing" in rule.errors().dump()
