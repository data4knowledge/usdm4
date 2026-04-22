"""Tests for RuleDDF00177 — Administration.dose iff Administration.route."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00177 import RuleDDF00177
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00177:
    def test_metadata(self):
        rule = RuleDDF00177()
        assert rule._rule == "DDF00177"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_both_set_passes(self):
        rule = RuleDDF00177()
        data = self._data([{"id": "A1", "dose": 5, "route": "oral"}])
        assert rule.validate({"data": data}) is True

    def test_neither_set_passes(self):
        rule = RuleDDF00177()
        data = self._data([{"id": "A1"}])
        assert rule.validate({"data": data}) is True

    def test_dose_without_route_fails(self):
        rule = RuleDDF00177()
        data = self._data([{"id": "A1", "dose": 5}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_route_without_dose_fails(self):
        rule = RuleDDF00177()
        data = self._data([{"id": "A1", "route": "oral"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
