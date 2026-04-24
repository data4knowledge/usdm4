"""Tests for RuleDDF00027 — siblings must not share previousId or nextId targets."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00027 import RuleDDF00027
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00027:
    def test_metadata(self):
        rule = RuleDDF00027()
        assert rule._rule == "DDF00027"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, by_klass, parent_dict):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        data._parent = parent_dict
        return data

    def test_non_dict_parent_is_skipped(self):
        rule = RuleDDF00027()
        data = self._data(
            {"Activity": [{"id": "A1", "previousId": "X"}]},
            parent_dict={"A1": None},
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_previous_id_fails(self):
        rule = RuleDDF00027()
        data = self._data(
            {
                "Activity": [
                    {"id": "A1", "previousId": "X"},
                    {"id": "A2", "previousId": "X"},
                ]
            },
            parent_dict={"A1": {"id": "P1"}, "A2": {"id": "P1"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
        assert "previousId" in rule.errors().dump()

    def test_duplicate_next_id_fails(self):
        rule = RuleDDF00027()
        data = self._data(
            {
                "Activity": [
                    {"id": "A1", "nextId": "X"},
                    {"id": "A2", "nextId": "X"},
                ]
            },
            parent_dict={"A1": {"id": "P1"}, "A2": {"id": "P1"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
        assert "nextId" in rule.errors().dump()

    def test_unique_links_pass(self):
        rule = RuleDDF00027()
        data = self._data(
            {
                "Activity": [
                    {"id": "A1", "previousId": "X"},
                    {"id": "A2", "previousId": "Y"},
                ]
            },
            parent_dict={"A1": {"id": "P1"}, "A2": {"id": "P1"}},
        )
        assert rule.validate({"data": data}) is True
