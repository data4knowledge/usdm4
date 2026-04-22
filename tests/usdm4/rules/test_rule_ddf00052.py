"""Tests for RuleDDF00052 — AliasCode.standardCodeAliases uniqueness."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00052 import RuleDDF00052
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00052:
    def test_metadata(self):
        rule = RuleDDF00052()
        assert rule._rule == "DDF00052"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "All standard code aliases referenced by an instance of the alias code class must be unique."
        )

    def _data(self, aliases):
        data = MagicMock()
        data.instances_by_klass.return_value = aliases
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_aliases_passes(self):
        rule = RuleDDF00052()
        data = self._data([{"id": "A1"}])  # no standardCodeAliases key
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_empty_aliases_passes(self):
        rule = RuleDDF00052()
        data = self._data([{"id": "A1", "standardCodeAliases": []}])
        assert rule.validate({"data": data}) is True

    def test_none_and_blank_values_skipped(self):
        """`None` and empty string entries don't count toward duplicates."""
        rule = RuleDDF00052()
        data = self._data(
            [
                {
                    "id": "A1",
                    "standardCodeAliases": [
                        {"code": None},
                        {"code": ""},
                        {"code": "X"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_non_dict_entry_used_directly(self):
        """A bare string is treated as the value itself — two matching strings dup."""
        rule = RuleDDF00052()
        data = self._data([{"id": "A1", "standardCodeAliases": ["X", "X"]}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_unique_aliases_pass(self):
        rule = RuleDDF00052()
        data = self._data(
            [
                {
                    "id": "A1",
                    "standardCodeAliases": [{"code": "X"}, {"code": "Y"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_aliases_fail(self):
        rule = RuleDDF00052()
        data = self._data(
            [
                {
                    "id": "A1",
                    "standardCodeAliases": [
                        {"code": "X"},
                        {"code": "X"},
                        {"code": "Y"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
