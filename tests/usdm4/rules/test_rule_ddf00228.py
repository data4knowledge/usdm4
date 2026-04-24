"""Tests for RuleDDF00228 — ObservationalStudyDesign.studyType populated."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00228 import RuleDDF00228
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00228:
    def test_metadata(self):
        rule = RuleDDF00228()
        assert rule._rule == "DDF00228"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_populated_passes(self):
        rule = RuleDDF00228()
        data = self._data([{"id": "O1", "studyType": {"code": "C1"}}])
        assert rule.validate({"data": data}) is True

    def test_empty_fails(self):
        rule = RuleDDF00228()
        data = self._data([{"id": "O1"}])
        assert rule.validate({"data": data}) is False
