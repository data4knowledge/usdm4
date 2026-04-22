"""Tests for RuleDDF00231 — BiospecimenRetention.isRetained → includesDNA bool."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00231 import RuleDDF00231
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00231:
    def test_metadata(self):
        rule = RuleDDF00231()
        assert rule._rule == "DDF00231"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_not_retained_skipped(self):
        rule = RuleDDF00231()
        data = self._data([{"id": "B1", "isRetained": False}])
        assert rule.validate({"data": data}) is True

    def test_retained_with_includes_dna_true_passes(self):
        rule = RuleDDF00231()
        data = self._data([{"id": "B1", "isRetained": True, "includesDNA": True}])
        assert rule.validate({"data": data}) is True

    def test_retained_with_includes_dna_false_passes(self):
        rule = RuleDDF00231()
        data = self._data([{"id": "B1", "isRetained": True, "includesDNA": False}])
        assert rule.validate({"data": data}) is True

    def test_retained_without_includes_dna_fails(self):
        rule = RuleDDF00231()
        data = self._data([{"id": "B1", "isRetained": True}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_retained_with_null_includes_dna_fails(self):
        rule = RuleDDF00231()
        data = self._data([{"id": "B1", "isRetained": True, "includesDNA": None}])
        assert rule.validate({"data": data}) is False
