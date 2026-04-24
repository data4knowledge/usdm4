"""Tests for RuleDDF00059 — StudyIntervention.codes uniqueness."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00059 import RuleDDF00059
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00059:
    def test_metadata(self):
        rule = RuleDDF00059()
        assert rule._rule == "DDF00059"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_unique_passes(self):
        rule = RuleDDF00059()
        data = self._data([{"id": "SI1", "codes": [{"code": "C1"}, {"code": "C2"}]}])
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00059()
        data = self._data([{"id": "SI1", "codes": [{"code": "C1"}, {"code": "C1"}]}])
        assert rule.validate({"data": data}) is False
        assert "Duplicate codes" in rule.errors().dump()
