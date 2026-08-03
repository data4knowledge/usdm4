"""Tests for RuleDDF00021 — previousId must not be self."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00021 import RuleDDF00021
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00021:
    def test_metadata(self):
        rule = RuleDDF00021()
        assert rule._rule == "DDF00021"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_previous_passes(self):
        rule = RuleDDF00021()
        data = self._data({"StudyEpoch": [{"id": "E1"}]})
        assert rule.validate({"data": data}) is True

    def test_distinct_previous_passes(self):
        rule = RuleDDF00021()
        data = self._data({"StudyEpoch": [{"id": "E1", "previousId": "E0"}]})
        assert rule.validate({"data": data}) is True

    def test_self_previous_fails(self):
        rule = RuleDDF00021()
        data = self._data({"StudyEpoch": [{"id": "E1", "previousId": "E1"}]})
        assert rule.validate({"data": data}) is False
        assert "refers to itself" in rule.errors().dump()
