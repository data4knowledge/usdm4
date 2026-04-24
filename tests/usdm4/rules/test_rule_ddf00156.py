"""Tests for RuleDDF00156 — Encounter.environmentalSettings uniqueness."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00156 import RuleDDF00156
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00156:
    def test_metadata(self):
        rule = RuleDDF00156()
        assert rule._rule == "DDF00156"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_unique_passes(self):
        rule = RuleDDF00156()
        data = self._data(
            [{"id": "E1", "environmentalSettings": [{"code": "A"}, {"code": "B"}]}]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00156()
        data = self._data(
            [{"id": "E1", "environmentalSettings": [{"code": "A"}, {"code": "A"}]}]
        )
        assert rule.validate({"data": data}) is False
        assert "Duplicate environmentalSettings" in rule.errors().dump()
