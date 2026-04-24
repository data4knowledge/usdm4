"""Tests for RuleDDF00096 — primary Endpoint must sit under a primary Objective."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00096 import RuleDDF00096
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00096:
    def test_metadata(self):
        rule = RuleDDF00096()
        assert rule._rule == "DDF00096"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, endpoints, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = endpoints
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda eid, _k: (parent_map or {}).get(eid)
        return data

    def test_non_primary_endpoint_skipped(self):
        rule = RuleDDF00096()
        data = self._data([{"id": "E1", "level": {"code": "OTHER"}}])
        assert rule.validate({"data": data}) is True

    def test_no_level_skipped(self):
        rule = RuleDDF00096()
        data = self._data([{"id": "E1"}])
        assert rule.validate({"data": data}) is True

    def test_primary_endpoint_under_primary_objective_passes(self):
        rule = RuleDDF00096()
        data = self._data(
            [{"id": "E1", "level": {"code": "C94496"}}],
            parent_map={"E1": {"id": "O1", "level": {"code": "C85826"}}},
        )
        assert rule.validate({"data": data}) is True

    def test_primary_endpoint_missing_objective_fails(self):
        rule = RuleDDF00096()
        data = self._data(
            [{"id": "E1", "level": {"code": "C94496"}}], parent_map={"E1": None}
        )
        assert rule.validate({"data": data}) is False
        assert "no parent Objective" in rule.errors().dump()

    def test_primary_endpoint_under_non_primary_objective_fails(self):
        rule = RuleDDF00096()
        data = self._data(
            [{"id": "E1", "level": {"code": "C94496"}}],
            parent_map={"E1": {"id": "O1", "level": {"code": "OTHER"}}},
        )
        assert rule.validate({"data": data}) is False
        assert "not a primary objective" in rule.errors().dump()
