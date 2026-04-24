"""Tests for RuleDDF00164 — NarrativeContent displaySectionNumber ↔ sectionNumber."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00164 import RuleDDF00164
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00164:
    def test_metadata(self):
        rule = RuleDDF00164()
        assert rule._rule == "DDF00164"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_both_set_passes(self):
        rule = RuleDDF00164()
        data = self._data(
            [{"id": "N1", "displaySectionNumber": True, "sectionNumber": "1.2"}]
        )
        assert rule.validate({"data": data}) is True

    def test_both_unset_passes(self):
        rule = RuleDDF00164()
        data = self._data([{"id": "N1"}])
        assert rule.validate({"data": data}) is True

    def test_display_without_number_fails(self):
        rule = RuleDDF00164()
        data = self._data(
            [{"id": "N1", "displaySectionNumber": True, "sectionNumber": ""}]
        )
        assert rule.validate({"data": data}) is False
        assert "sectionNumber is missing" in rule.errors().dump()

    def test_number_without_display_fails(self):
        rule = RuleDDF00164()
        data = self._data(
            [{"id": "N1", "displaySectionNumber": False, "sectionNumber": "2"}]
        )
        assert rule.validate({"data": data}) is False
        assert "displaySectionNumber is missing" in rule.errors().dump()
