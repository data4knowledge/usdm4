"""Tests for RuleDDF00090 — Activity.bcCategories uniqueness."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00090 import RuleDDF00090
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00090:
    def test_metadata(self):
        rule = RuleDDF00090()
        assert rule._rule == "DDF00090"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "The same Biomedical Concept Category must not be referenced more than once from the same activity."
        )

    def _data(self, activities):
        data = MagicMock()
        data.instances_by_klass.return_value = activities
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_categories_passes(self):
        rule = RuleDDF00090()
        data = self._data([{"id": "ACT1"}])
        assert rule.validate({"data": data}) is True

    def test_empty_categories_passes(self):
        rule = RuleDDF00090()
        data = self._data([{"id": "ACT1", "bcCategories": []}])
        assert rule.validate({"data": data}) is True

    def test_none_and_blank_values_skipped(self):
        rule = RuleDDF00090()
        data = self._data(
            [
                {
                    "id": "ACT1",
                    "bcCategories": [{"id": None}, {"id": ""}, {"id": "B1"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_non_dict_entry_used_directly(self):
        rule = RuleDDF00090()
        data = self._data([{"id": "ACT1", "bcCategories": ["B1", "B1"]}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_unique_categories_pass(self):
        rule = RuleDDF00090()
        data = self._data(
            [{"id": "ACT1", "bcCategories": [{"id": "B1"}, {"id": "B2"}]}]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_categories_fail(self):
        rule = RuleDDF00090()
        data = self._data(
            [
                {
                    "id": "ACT1",
                    "bcCategories": [{"id": "B1"}, {"id": "B1"}, {"id": "B2"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
