"""Tests for RuleDDF00158 — ObservationalStudyDesign.criteria populated."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00158 import RuleDDF00158
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00158:
    def test_metadata(self):
        rule = RuleDDF00158()
        assert rule._rule == "DDF00158"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_populated_passes(self):
        rule = RuleDDF00158()
        data = self._data([{"id": "D1", "criteria": ["C1"]}])
        assert rule.validate({"data": data}) is True

    def test_empty_fails(self):
        rule = RuleDDF00158()
        data = self._data([{"id": "D1"}])
        assert rule.validate({"data": data}) is False
