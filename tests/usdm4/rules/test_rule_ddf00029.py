"""Tests for RuleDDF00029 — Encounter.previousId/nextId same-StudyDesign."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00029 import RuleDDF00029
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00029:
    def test_metadata(self):
        rule = RuleDDF00029()
        assert rule._rule == "DDF00029"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, encounters, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = encounters
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda eid, _k: (parent_map or {}).get(eid)
        return data

    def test_no_design_skipped(self):
        rule = RuleDDF00029()
        data = self._data([{"id": "E1", "previousId": "E0"}], parent_map={"E1": None})
        assert rule.validate({"data": data}) is True

    def test_target_no_design_skipped(self):
        rule = RuleDDF00029()
        data = self._data(
            [{"id": "E1", "nextId": "E2"}],
            parent_map={"E1": {"id": "SD1"}, "E2": None},
        )
        assert rule.validate({"data": data}) is True

    def test_same_design_passes(self):
        rule = RuleDDF00029()
        data = self._data(
            [{"id": "E1", "previousId": "E0", "nextId": "E2"}],
            parent_map={
                "E1": {"id": "SD1"},
                "E0": {"id": "SD1"},
                "E2": {"id": "SD1"},
            },
        )
        assert rule.validate({"data": data}) is True

    def test_cross_design_fails(self):
        rule = RuleDDF00029()
        data = self._data(
            [{"id": "E1", "nextId": "E2"}],
            parent_map={"E1": {"id": "SD1"}, "E2": {"id": "SD2"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
        assert "different StudyDesign" in rule.errors().dump()
