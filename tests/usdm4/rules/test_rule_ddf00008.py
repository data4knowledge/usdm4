"""Tests for RuleDDF00008 — SAI exactly-one of defaultConditionId / timelineExitId."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00008 import RuleDDF00008
from usdm4.rules.rule_template import RuleTemplate


def _data(items):
    data = MagicMock()
    data.instances_by_klass.return_value = items
    data.path_by_id.return_value = "$.path"
    return data


class TestRuleDDF00008:
    def test_metadata(self):
        rule = RuleDDF00008()
        assert rule._rule == "DDF00008"
        assert rule._level == RuleTemplate.ERROR

    def test_only_condition_passes(self):
        rule = RuleDDF00008()
        data = _data([{"id": "S1", "defaultConditionId": "C1"}])
        assert rule.validate({"data": data}) is True

    def test_only_exit_passes(self):
        rule = RuleDDF00008()
        data = _data([{"id": "S1", "timelineExitId": "T1"}])
        assert rule.validate({"data": data}) is True

    def test_both_set_fails(self):
        rule = RuleDDF00008()
        data = _data([{"id": "S1", "defaultConditionId": "C1", "timelineExitId": "T1"}])
        assert rule.validate({"data": data}) is False
        assert "Both" in rule.errors().dump()

    def test_neither_set_fails(self):
        """Regression: sample 3 surfaced 4 SAIs with neither id set. The
        old implementation silently passed these because it only checked
        the 'both set' case."""
        rule = RuleDDF00008()
        data = _data([{"id": "S1"}])
        assert rule.validate({"data": data}) is False
        assert "Neither" in rule.errors().dump()

    def test_both_null_fails(self):
        rule = RuleDDF00008()
        data = _data([{"id": "S1", "defaultConditionId": None, "timelineExitId": None}])
        assert rule.validate({"data": data}) is False

    def test_both_empty_string_fails(self):
        rule = RuleDDF00008()
        data = _data([{"id": "S1", "defaultConditionId": "", "timelineExitId": ""}])
        assert rule.validate({"data": data}) is False

    def test_mix_of_instances_reports_all_failures(self):
        rule = RuleDDF00008()
        data = _data(
            [
                {"id": "S1", "defaultConditionId": "C1"},  # pass
                {"id": "S2", "timelineExitId": "T1"},  # pass
                {"id": "S3"},  # fail (neither)
                {
                    "id": "S4",
                    "defaultConditionId": "C2",
                    "timelineExitId": "T2",
                },  # fail (both)
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
