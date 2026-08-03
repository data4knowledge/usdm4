"""Tests for RuleDDF00050 — StudyArm populations id references must resolve."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00050 import RuleDDF00050
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00050:
    def test_metadata(self):
        rule = RuleDDF00050()
        assert rule._rule == "DDF00050"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "A study arm must only reference study populations or cohorts that are defined within the same study design as the study arm."
        )

    def _data(self, arms, resolvable_ids=None):
        data = MagicMock()
        data.instances_by_klass.return_value = arms
        data.path_by_id.return_value = "$.path"
        resolvable = resolvable_ids or set()
        data.instance_by_id.side_effect = lambda i: (
            {"id": i} if i in resolvable else None
        )
        return data

    def test_empty_or_none_populations_skipped(self):
        rule = RuleDDF00050()
        data = self._data(
            [
                {"id": "A1", "populations": None},
                {"id": "A2", "populations": ""},
                {"id": "A3", "populations": []},
                {"id": "A4", "populations": {}},
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_scalar_populations_resolved(self):
        rule = RuleDDF00050()
        data = self._data([{"id": "A1", "populations": "P1"}], resolvable_ids={"P1"})
        assert rule.validate({"data": data}) is True

    def test_list_populations_all_resolved_passes(self):
        rule = RuleDDF00050()
        data = self._data(
            [{"id": "A1", "populations": ["P1", "P2"]}],
            resolvable_ids={"P1", "P2"},
        )
        assert rule.validate({"data": data}) is True

    def test_unresolved_id_fails(self):
        rule = RuleDDF00050()
        data = self._data(
            [{"id": "A1", "populations": ["P1", "P2"]}],
            resolvable_ids={"P1"},
        )
        assert rule.validate({"data": data}) is False
        assert "unresolved id 'P2'" in rule.errors().dump()
