"""Tests for RuleDDF00171 — Abbreviation.expandedText unique per StudyVersion."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00171 import RuleDDF00171
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00171:
    def test_metadata(self):
        rule = RuleDDF00171()
        assert rule._rule == "DDF00171"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda i, _k: (parent_map or {}).get(i)
        return data

    def test_no_scope_skipped(self):
        rule = RuleDDF00171()
        data = self._data(
            [{"id": "A1", "expandedText": "expanded"}], parent_map={"A1": None}
        )
        assert rule.validate({"data": data}) is True

    def test_empty_value_skipped(self):
        rule = RuleDDF00171()
        data = self._data(
            [{"id": "A1", "expandedText": ""}], parent_map={"A1": {"id": "SV1"}}
        )
        assert rule.validate({"data": data}) is True

    def test_unique_passes(self):
        rule = RuleDDF00171()
        data = self._data(
            [
                {"id": "A1", "expandedText": "Alpha"},
                {"id": "A2", "expandedText": "Beta"},
            ],
            parent_map={"A1": {"id": "SV1"}, "A2": {"id": "SV1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00171()
        data = self._data(
            [
                {"id": "A1", "expandedText": "Same"},
                {"id": "A2", "expandedText": "Same"},
            ],
            parent_map={"A1": {"id": "SV1"}, "A2": {"id": "SV1"}},
        )
        assert rule.validate({"data": data}) is False
