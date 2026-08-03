"""Tests for RuleDDF00106 — ScheduledActivityInstance.encounter same-design."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00106 import RuleDDF00106
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00106:
    def test_metadata(self):
        rule = RuleDDF00106()
        assert rule._rule == "DDF00106"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, by_klass, id_map=None, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda tid: (id_map or {}).get(tid)
        data.parent_by_klass.side_effect = lambda tid, _kl: (parent_map or {}).get(tid)
        return data

    def test_no_encounter_id_skipped(self):
        rule = RuleDDF00106()
        data = self._data(
            {"ScheduledActivityInstance": [{"id": "SAI1", "instanceType": "SAI"}]}
        )
        assert rule.validate({"data": data}) is True

    def test_encounter_unresolved_skipped(self):
        rule = RuleDDF00106()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "encounterId": "missing"}
                ]
            },
            id_map={},
        )
        assert rule.validate({"data": data}) is True

    def test_both_parents_missing_fails(self):
        rule = RuleDDF00106()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "encounterId": "ENC1"}
                ]
            },
            id_map={"ENC1": {"id": "ENC1", "instanceType": "Encounter"}},
            parent_map={},
        )
        assert rule.validate({"data": data}) is False
        assert "SAI and Encounter missing parents" in rule.errors().dump()

    def test_item_parent_missing_fails(self):
        rule = RuleDDF00106()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "encounterId": "ENC1"}
                ]
            },
            id_map={"ENC1": {"id": "ENC1", "instanceType": "Encounter"}},
            parent_map={"ENC1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is False
        assert "SAI missing parent" in rule.errors().dump()

    def test_encounter_parent_missing_fails(self):
        rule = RuleDDF00106()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "encounterId": "ENC1"}
                ]
            },
            id_map={"ENC1": {"id": "ENC1", "instanceType": "Encounter"}},
            parent_map={"SAI1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is False
        assert "Encounter missing parent" in rule.errors().dump()

    def test_different_parents_fail(self):
        rule = RuleDDF00106()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "encounterId": "ENC1"}
                ]
            },
            id_map={"ENC1": {"id": "ENC1", "instanceType": "Encounter"}},
            parent_map={"SAI1": {"id": "SD1"}, "ENC1": {"id": "SD2"}},
        )
        assert rule.validate({"data": data}) is False
        assert "different study design" in rule.errors().dump()

    def test_same_parent_passes(self):
        rule = RuleDDF00106()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "encounterId": "ENC1"}
                ]
            },
            id_map={"ENC1": {"id": "ENC1", "instanceType": "Encounter"}},
            parent_map={"SAI1": {"id": "SD1"}, "ENC1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is True
