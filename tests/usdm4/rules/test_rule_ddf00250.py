"""Tests for RuleDDF00250 — EligibilityCriterion not in both pop and cohort."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00250 import RuleDDF00250
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00250:
    def test_metadata(self):
        rule = RuleDDF00250()
        assert rule._rule == "DDF00250"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_only_pop_passes(self):
        rule = RuleDDF00250()
        data = self._data(
            {
                "StudyDesignPopulation": [{"id": "P1", "criterionIds": ["EC1"]}],
                "StudyCohort": [],
                "EligibilityCriterion": [{"id": "EC1"}],
            }
        )
        assert rule.validate({"data": data}) is True

    def test_only_cohort_passes(self):
        rule = RuleDDF00250()
        data = self._data(
            {
                "StudyCohort": [{"id": "C1", "criterionIds": ["EC1"]}],
                "EligibilityCriterion": [{"id": "EC1"}],
            }
        )
        assert rule.validate({"data": data}) is True

    def test_both_fails(self):
        rule = RuleDDF00250()
        data = self._data(
            {
                "StudyDesignPopulation": [{"id": "P1", "criterionIds": ["EC1"]}],
                "StudyCohort": [{"id": "C1", "criterionIds": ["EC1"]}],
                "EligibilityCriterion": [{"id": "EC1"}],
            }
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
