"""Tests for RuleDDF00040 — StudyElement.elements must be populated."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00040 import RuleDDF00040
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00040:
    def test_metadata(self):
        rule = RuleDDF00040()
        assert rule._rule == "DDF00040"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_populated_passes(self):
        rule = RuleDDF00040()
        data = self._data([{"id": "E1", "elements": ["X"]}])
        assert rule.validate({"data": data}) is True

    def test_empty_fails(self):
        rule = RuleDDF00040()
        data = self._data([{"id": "E1", "elements": []}])
        assert rule.validate({"data": data}) is False
        assert "missing or empty" in rule.errors().dump()

    def test_absent_fails(self):
        rule = RuleDDF00040()
        data = self._data([{"id": "E1"}])
        assert rule.validate({"data": data}) is False
