"""Tests for RuleDDF00252 — StudyElement.studyInterventions id refs."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00252 import RuleDDF00252
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00252:
    def test_metadata(self):
        rule = RuleDDF00252()
        assert rule._rule == "DDF00252"
        assert rule._level == RuleTemplate.ERROR
        assert (
            rule._rule_text
            == "A study element must only reference study interventions that are referenced by the same study design as the study element."
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
        rule = RuleDDF00252()
        data = self._data([{"id": "E1", "studyInterventions": []}])
        assert rule.validate({"data": data}) is True

    def test_resolved_passes(self):
        rule = RuleDDF00252()
        data = self._data(
            [{"id": "E1", "studyInterventions": ["I1"]}], resolvable={"I1"}
        )
        assert rule.validate({"data": data}) is True

    def test_unresolved_fails(self):
        rule = RuleDDF00252()
        data = self._data(
            [{"id": "E1", "studyInterventions": ["I1", "I2"]}], resolvable={"I1"}
        )
        assert rule.validate({"data": data}) is False
        assert (
            "studyInterventions references unresolved id 'I2'" in rule.errors().dump()
        )
