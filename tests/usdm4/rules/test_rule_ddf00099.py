"""Tests for RuleDDF00099 — every StudyEpoch is referenced by some SAI."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00099 import RuleDDF00099
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00099:
    def test_metadata(self):
        rule = RuleDDF00099()
        assert rule._rule == "DDF00099"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_referenced_passes(self):
        rule = RuleDDF00099()
        data = self._data(
            {
                "ScheduledActivityInstance": [{"id": "S1", "epochId": "E1"}],
                "StudyEpoch": [{"id": "E1"}],
            }
        )
        assert rule.validate({"data": data}) is True

    def test_unreferenced_fails(self):
        rule = RuleDDF00099()
        data = self._data(
            {
                "ScheduledActivityInstance": [{"id": "S1", "epochId": "E1"}],
                "StudyEpoch": [{"id": "E1"}, {"id": "E2"}],
            }
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() >= 1

    def test_empty_epoch_id_ignored(self):
        rule = RuleDDF00099()
        data = self._data(
            {
                "ScheduledActivityInstance": [{"id": "S1", "epochId": None}],
                "StudyEpoch": [{"id": "E1"}],
            }
        )
        assert rule.validate({"data": data}) is False
