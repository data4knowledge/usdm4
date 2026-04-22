"""Tests for RuleDDF00010 — uniqueness of name per instanceType."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00010 import RuleDDF00010
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00010:
    def test_metadata(self):
        rule = RuleDDF00010()
        assert rule._rule == "DDF00010"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, ids):
        data = MagicMock()
        data._ids = ids
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_dict_skipped(self):
        rule = RuleDDF00010()
        data = self._data({"x": "not a dict"})
        assert rule.validate({"data": data}) is True

    def test_missing_name_or_type_skipped(self):
        rule = RuleDDF00010()
        data = self._data(
            {
                "a": {"id": "a", "instanceType": "X"},
                "b": {"id": "b", "name": "same"},
            }
        )
        assert rule.validate({"data": data}) is True

    def test_unique_names_pass(self):
        rule = RuleDDF00010()
        data = self._data(
            {
                "a": {"id": "a", "instanceType": "X", "name": "alpha"},
                "b": {"id": "b", "instanceType": "X", "name": "beta"},
            }
        )
        assert rule.validate({"data": data}) is True

    def test_same_name_different_types_pass(self):
        rule = RuleDDF00010()
        data = self._data(
            {
                "a": {"id": "a", "instanceType": "X", "name": "same"},
                "b": {"id": "b", "instanceType": "Y", "name": "same"},
            }
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_name_same_type_fails(self):
        rule = RuleDDF00010()
        data = self._data(
            {
                "a": {"id": "a", "instanceType": "X", "name": "dup"},
                "b": {"id": "b", "instanceType": "X", "name": "dup"},
            }
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
        assert "not unique" in rule.errors().dump()
