"""Tests for RuleDDF00023 — consistent previousId/nextId back-links."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00023 import RuleDDF00023
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00023:
    def test_metadata(self):
        rule = RuleDDF00023()
        assert rule._rule == "DDF00023"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items_by_klass, by_id=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: items_by_klass.get(k, [])
        data.instance_by_id.side_effect = lambda i: (by_id or {}).get(i)
        data.path_by_id.return_value = "$.path"
        return data

    def test_empty_scope_passes(self):
        rule = RuleDDF00023()
        data = self._data({})
        assert rule.validate({"data": data}) is True

    def test_consistent_links_pass(self):
        rule = RuleDDF00023()
        data = self._data(
            {
                "Activity": [
                    {"id": "A1", "previousId": "A0", "nextId": "A2"},
                ]
            },
            by_id={
                "A0": {"id": "A0", "nextId": "A1"},
                "A2": {"id": "A2", "previousId": "A1"},
            },
        )
        assert rule.validate({"data": data}) is True

    def test_previous_mismatch_fails(self):
        rule = RuleDDF00023()
        data = self._data(
            {"Activity": [{"id": "A1", "previousId": "A0"}]},
            by_id={"A0": {"id": "A0", "nextId": "OTHER"}},
        )
        assert rule.validate({"data": data}) is False
        assert "previousId" in rule.errors().dump()

    def test_next_mismatch_fails(self):
        rule = RuleDDF00023()
        data = self._data(
            {"StudyEpoch": [{"id": "E1", "nextId": "E2"}]},
            by_id={"E2": {"id": "E2", "previousId": "OTHER"}},
        )
        assert rule.validate({"data": data}) is False
        assert "nextId" in rule.errors().dump()

    def test_missing_backlink_skipped(self):
        rule = RuleDDF00023()
        data = self._data(
            {"Activity": [{"id": "A1", "previousId": "A0", "nextId": "A2"}]},
            by_id={"A0": {"id": "A0"}, "A2": {"id": "A2"}},
        )
        assert rule.validate({"data": data}) is True
