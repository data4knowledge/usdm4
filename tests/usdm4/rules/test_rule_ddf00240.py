"""Tests for RuleDDF00240 — Procedure.studyIntervention id refs."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00240 import RuleDDF00240
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00240:
    def test_metadata(self):
        rule = RuleDDF00240()
        assert rule._rule == "DDF00240"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "A procedure must only reference a study intervention that is referenced by the same study design as the activity within which the procedure is defined."
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
        rule = RuleDDF00240()
        data = self._data([{"id": "P1", "studyIntervention": None}])
        assert rule.validate({"data": data}) is True

    def test_resolved_passes(self):
        rule = RuleDDF00240()
        data = self._data([{"id": "P1", "studyIntervention": "I1"}], resolvable={"I1"})
        assert rule.validate({"data": data}) is True

    def test_unresolved_fails(self):
        rule = RuleDDF00240()
        data = self._data([{"id": "P1", "studyIntervention": "I1"}])
        assert rule.validate({"data": data}) is False
        assert "studyIntervention references unresolved id 'I1'" in rule.errors().dump()
