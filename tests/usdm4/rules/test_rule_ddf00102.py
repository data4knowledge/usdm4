"""Tests for RuleDDF00102 — ScheduledActivityInstance.timelineExit id refs."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00102 import RuleDDF00102
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00102:
    def test_metadata(self):
        rule = RuleDDF00102()
        assert rule._rule == "DDF00102"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "A scheduled activity instance must only reference a timeline exit that is defined within the same schedule timeline as the scheduled activity instance."
        )

    def _data(self, items, resolvable=None):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        resolvable = resolvable or set()
        data.instance_by_id.side_effect = lambda i: (
            {"id": i} if i in resolvable else None
        )
        return data

    def test_empty_skipped(self):
        rule = RuleDDF00102()
        data = self._data([{"id": "S1", "timelineExit": ""}])
        assert rule.validate({"data": data}) is True

    def test_resolved_passes(self):
        rule = RuleDDF00102()
        data = self._data([{"id": "S1", "timelineExit": "X1"}], resolvable={"X1"})
        assert rule.validate({"data": data}) is True

    def test_unresolved_fails(self):
        rule = RuleDDF00102()
        data = self._data([{"id": "S1", "timelineExit": "X1"}])
        assert rule.validate({"data": data}) is False
        assert "timelineExit references unresolved id 'X1'" in rule.errors().dump()
