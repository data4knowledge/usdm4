"""Tests for RuleDDF00260 — id values must not contain spaces."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00260 import RuleDDF00260
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00260:
    def test_metadata(self):
        rule = RuleDDF00260()
        assert rule._rule == "DDF00260"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, ids):
        data = MagicMock()
        data._ids = ids
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_spaces_passes(self):
        rule = RuleDDF00260()
        data = self._data(
            {
                "A_1": {"id": "A_1", "instanceType": "X"},
                "B-2": {"id": "B-2", "instanceType": "Y"},
            }
        )
        assert rule.validate({"data": data}) is True

    def test_space_fails(self):
        rule = RuleDDF00260()
        data = self._data({"A 1": {"id": "A 1", "instanceType": "X"}})
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_non_dict_value_treated_as_unknown(self):
        rule = RuleDDF00260()
        data = self._data({"B 2": "not a dict"})
        assert rule.validate({"data": data}) is False

    def test_non_string_id_skipped(self):
        rule = RuleDDF00260()
        data = self._data({42: {"id": 42}})
        assert rule.validate({"data": data}) is True
