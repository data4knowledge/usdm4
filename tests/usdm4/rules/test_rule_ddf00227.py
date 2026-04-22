"""Tests for RuleDDF00227 — InterventionalStudyDesign.studyType populated."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00227 import RuleDDF00227
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00227:
    def test_metadata(self):
        rule = RuleDDF00227()
        assert rule._rule == "DDF00227"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_populated_passes(self):
        rule = RuleDDF00227()
        data = self._data([{"id": "I1", "studyType": {"code": "C1"}}])
        assert rule.validate({"data": data}) is True

    def test_empty_fails(self):
        rule = RuleDDF00227()
        data = self._data([{"id": "I1"}])
        assert rule.validate({"data": data}) is False
