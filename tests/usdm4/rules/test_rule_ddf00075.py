"""Tests for RuleDDF00075 — Activity should reference at least one leaf."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00075 import RuleDDF00075
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00075:
    def test_metadata(self):
        rule = RuleDDF00075()
        assert rule._rule == "DDF00075"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, activities):
        data = MagicMock()
        data.instances_by_klass.return_value = activities
        data.path_by_id.return_value = "$.path"
        return data

    def test_wrapper_skipped(self):
        rule = RuleDDF00075()
        data = self._data([{"id": "A1", "childIds": ["A2"]}])
        assert rule.validate({"data": data}) is True

    def test_leaf_with_refs_passes(self):
        rule = RuleDDF00075()
        data = self._data([{"id": "A1", "biomedicalConceptIds": ["B1"]}])
        assert rule.validate({"data": data}) is True

    def test_leaf_without_refs_fails(self):
        rule = RuleDDF00075()
        data = self._data([{"id": "A1"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
