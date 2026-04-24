"""Tests for RuleDDF00083 — global id uniqueness within the study version."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00083 import RuleDDF00083
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00083:
    def test_metadata(self):
        rule = RuleDDF00083()
        assert rule._rule == "DDF00083"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, tree):
        data = MagicMock()
        data.data = tree
        return data

    def test_unique_ids_pass(self):
        rule = RuleDDF00083()
        tree = {
            "id": "A",
            "instanceType": "Root",
            "children": [
                {"id": "B", "instanceType": "Child"},
                {"id": "C", "instanceType": "Child"},
            ],
        }
        assert rule.validate({"data": self._data(tree)}) is True

    def test_duplicate_id_fails(self):
        rule = RuleDDF00083()
        tree = {
            "id": "A",
            "instanceType": "Root",
            "children": [
                {"id": "DUP", "instanceType": "Child"},
                {"id": "DUP", "instanceType": "Child"},
            ],
        }
        assert rule.validate({"data": self._data(tree)}) is False
        assert rule.errors().count() == 2
        assert "not unique" in rule.errors().dump()

    def test_nested_lists_and_dicts(self):
        rule = RuleDDF00083()
        tree = {
            "id": "A",
            "instanceType": "Root",
            "nested": {
                "more": [
                    {"id": "X", "instanceType": "Deep"},
                    {"id": "X", "instanceType": "Deep"},
                ]
            },
        }
        assert rule.validate({"data": self._data(tree)}) is False
        assert rule.errors().count() == 2

    def test_dict_without_instance_type_is_ignored(self):
        rule = RuleDDF00083()
        # A dict carrying `id` but not `instanceType` should NOT be counted
        # (mirrors the CORE filter `[id and instanceType]`).
        tree = {
            "id": "A",
            "instanceType": "Root",
            "meta": {"id": "A"},  # same id, no instanceType — ignored
        }
        assert rule.validate({"data": self._data(tree)}) is True

    def test_non_string_ids_ignored(self):
        rule = RuleDDF00083()
        tree = {
            "id": 1,
            "instanceType": "Root",
            "children": [{"id": 1, "instanceType": "Child"}],
        }
        assert rule.validate({"data": self._data(tree)}) is True

    def test_missing_data_attr_passes(self):
        rule = RuleDDF00083()
        data = MagicMock(spec=["foo"])  # no .data attribute
        assert rule.validate({"data": data}) is True
