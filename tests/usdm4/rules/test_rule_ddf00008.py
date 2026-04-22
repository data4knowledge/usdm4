"""Tests for RuleDDF00008 — SAI timelineExit XOR defaultCondition."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00008 import RuleDDF00008
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00008:
    def test_metadata(self):
        rule = RuleDDF00008()
        assert rule._rule == "DDF00008"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items, by_id=None):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda i: (by_id or {}).get(i)
        return data

    def test_only_one_passes(self):
        rule = RuleDDF00008()
        data = self._data(
            [
                {
                    "id": "S1",
                    "instanceType": "SAI",
                    "timelineExitId": "T1",
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_both_fails_when_both_exist(self):
        rule = RuleDDF00008()
        data = self._data(
            [
                {
                    "id": "S1",
                    "instanceType": "SAI",
                    "timelineExitId": "T1",
                    "defaultConditionId": "C1",
                }
            ],
            by_id={"T1": {"id": "T1"}, "C1": {"id": "C1"}},
        )
        assert rule.validate({"data": data}) is False
        assert "both exist" in rule.errors().dump()

    def test_both_ids_but_missing_instance_passes(self):
        rule = RuleDDF00008()
        data = self._data(
            [
                {
                    "id": "S1",
                    "instanceType": "SAI",
                    "timelineExitId": "T1",
                    "defaultConditionId": "C1",
                }
            ],
            by_id={"T1": None, "C1": {"id": "C1"}},
        )
        assert rule.validate({"data": data}) is True
