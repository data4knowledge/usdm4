"""Tests for RuleDDF00054 — Encounter.contactModes uniqueness."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00054 import RuleDDF00054
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00054:
    def test_metadata(self):
        rule = RuleDDF00054()
        assert rule._rule == "DDF00054"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_unique_passes(self):
        rule = RuleDDF00054()
        data = self._data(
            [{"id": "E1", "contactModes": [{"code": "A"}, {"code": "B"}]}]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00054()
        data = self._data(
            [{"id": "E1", "contactModes": [{"code": "A"}, {"code": "A"}]}]
        )
        assert rule.validate({"data": data}) is False
        assert "Duplicate contactModes" in rule.errors().dump()

    def test_none_filtered(self):
        rule = RuleDDF00054()
        data = self._data(
            [
                {
                    "id": "E1",
                    "contactModes": [{"code": None}, {"code": ""}, {"code": "A"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
