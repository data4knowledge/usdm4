"""Tests for RuleDDF00105 — ScheduledActivity/DecisionInstance.epoch same-design."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00105 import RuleDDF00105
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00105:
    def test_metadata(self):
        rule = RuleDDF00105()
        assert rule._rule == "DDF00105"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, by_klass, id_map=None, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda tid: (id_map or {}).get(tid)
        data.parent_by_klass.side_effect = lambda tid, _kl: (parent_map or {}).get(tid)
        return data

    def test_no_epoch_id_skipped(self):
        rule = RuleDDF00105()
        data = self._data(
            {"ScheduledActivityInstance": [{"id": "SAI1", "instanceType": "SAI"}]}
        )
        assert rule.validate({"data": data}) is True

    def test_epoch_unresolved_skipped(self):
        """If `instance_by_id` returns None (epoch doesn't exist) — skip silently.
        Other rules catch unresolved references."""
        rule = RuleDDF00105()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "epochId": "missing"}
                ]
            },
            id_map={},
        )
        assert rule.validate({"data": data}) is True

    def test_both_parents_missing_fails(self):
        rule = RuleDDF00105()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "epochId": "E1"}
                ]
            },
            id_map={"E1": {"id": "E1", "instanceType": "StudyEpoch"}},
            parent_map={},
        )
        assert rule.validate({"data": data}) is False
        assert "SAI and StudyEpoch missing parents" in rule.errors().dump()

    def test_item_parent_missing_fails(self):
        rule = RuleDDF00105()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "epochId": "E1"}
                ]
            },
            id_map={"E1": {"id": "E1", "instanceType": "StudyEpoch"}},
            parent_map={"E1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is False
        assert "SAI missing parent" in rule.errors().dump()

    def test_epoch_parent_missing_fails(self):
        rule = RuleDDF00105()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "epochId": "E1"}
                ]
            },
            id_map={"E1": {"id": "E1", "instanceType": "StudyEpoch"}},
            parent_map={"SAI1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is False
        assert "StudyEpoch missing parent" in rule.errors().dump()

    def test_different_parents_fail(self):
        rule = RuleDDF00105()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "epochId": "E1"}
                ]
            },
            id_map={"E1": {"id": "E1", "instanceType": "StudyEpoch"}},
            parent_map={"SAI1": {"id": "SD1"}, "E1": {"id": "SD2"}},
        )
        assert rule.validate({"data": data}) is False
        assert "different study design" in rule.errors().dump()

    def test_same_parent_passes(self):
        rule = RuleDDF00105()
        data = self._data(
            {
                "ScheduledActivityInstance": [
                    {"id": "SAI1", "instanceType": "SAI", "epochId": "E1"}
                ]
            },
            id_map={"E1": {"id": "E1", "instanceType": "StudyEpoch"}},
            parent_map={"SAI1": {"id": "SD1"}, "E1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_scheduled_decision_instances_also_checked(self):
        """The rule concatenates SAI and SDI — a SDI with a mismatched epoch fails."""
        rule = RuleDDF00105()
        data = self._data(
            {
                "ScheduledActivityInstance": [],
                "ScheduledDecisionInstance": [
                    {"id": "SDI1", "instanceType": "SDI", "epochId": "E1"}
                ],
            },
            id_map={"E1": {"id": "E1", "instanceType": "StudyEpoch"}},
            parent_map={"SDI1": {"id": "SD1"}, "E1": {"id": "SD2"}},
        )
        assert rule.validate({"data": data}) is False
