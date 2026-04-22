"""Tests for RuleDDF00013 — BCP isRequired => isEnabled."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00013 import RuleDDF00013
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00013:
    def test_metadata(self):
        rule = RuleDDF00013()
        assert rule._rule == "DDF00013"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_required_and_enabled_passes(self):
        rule = RuleDDF00013()
        data = self._data([{"id": "B1", "isRequired": True, "isEnabled": True}])
        assert rule.validate({"data": data}) is True

    def test_not_required_passes(self):
        rule = RuleDDF00013()
        data = self._data([{"id": "B1", "isRequired": False, "isEnabled": False}])
        assert rule.validate({"data": data}) is True

    def test_required_not_enabled_fails(self):
        rule = RuleDDF00013()
        data = self._data([{"id": "B1", "isRequired": True, "isEnabled": False}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
