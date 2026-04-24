"""Tests for RuleDDF00014 — BiomedicalConceptCategory needs member or child."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00014 import RuleDDF00014
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00014:
    def test_metadata(self):
        rule = RuleDDF00014()
        assert rule._rule == "DDF00014"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_neither_members_nor_children_fails(self):
        rule = RuleDDF00014()
        data = self._data([{"id": "C1"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_member_alone_passes(self):
        rule = RuleDDF00014()
        data = self._data([{"id": "C1", "memberIds": ["M1"]}])
        assert rule.validate({"data": data}) is True

    def test_child_alone_passes(self):
        rule = RuleDDF00014()
        data = self._data([{"id": "C1", "childIds": ["C2"]}])
        assert rule.validate({"data": data}) is True
