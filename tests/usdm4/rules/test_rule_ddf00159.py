"""Tests for RuleDDF00159 — EligibilityCriterion not referenced by both pop & cohort."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00159 import RuleDDF00159
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00159:
    def test_metadata(self):
        rule = RuleDDF00159()
        assert rule._rule == "DDF00159"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, interventional=None, observational=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "InterventionalStudyDesign": interventional or [],
            "ObservationalStudyDesign": observational or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_population_skipped(self):
        rule = RuleDDF00159()
        data = self._data(interventional=[{"id": "SD1"}])
        assert rule.validate({"data": data}) is True

    def test_non_dict_population_skipped(self):
        rule = RuleDDF00159()
        data = self._data(interventional=[{"id": "SD1", "population": "bad"}])
        assert rule.validate({"data": data}) is True

    def test_disjoint_ids_pass(self):
        rule = RuleDDF00159()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "population": {
                        "criterionIds": ["C1"],
                        "cohorts": [{"criterionIds": ["C2"]}],
                    },
                    "eligibilityCriteria": [{"id": "C1"}, {"id": "C2"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_overlap_fails(self):
        rule = RuleDDF00159()
        data = self._data(
            observational=[
                {
                    "id": "SD1",
                    "population": {
                        "criterionIds": ["C1", "C2"],
                        "cohorts": [{"criterionIds": ["C1"]}],
                    },
                    "eligibilityCriteria": [{"id": "C1"}, {"id": "C2"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
