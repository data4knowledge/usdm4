"""Tests for RuleDDF00211 — ProductOrganizationRole.appliesTo populated."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00211 import RuleDDF00211
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00211:
    def test_metadata(self):
        rule = RuleDDF00211()
        assert rule._rule == "DDF00211"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_populated_passes(self):
        rule = RuleDDF00211()
        data = self._data([{"id": "R1", "appliesTo": ["X"]}])
        assert rule.validate({"data": data}) is True

    def test_empty_fails(self):
        rule = RuleDDF00211()
        data = self._data([{"id": "R1"}])
        assert rule.validate({"data": data}) is False
