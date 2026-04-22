"""Tests for RuleDDF00213 — multi-group InterventionalStudyDesign expects >1 intervention."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00213 import RuleDDF00213
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00213:
    def test_metadata(self):
        rule = RuleDDF00213()
        assert rule._rule == "DDF00213"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_interventional_skipped(self):
        rule = RuleDDF00213()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyInterventions": [],
                    "studyDesigns": [{"id": "D1", "studyType": {"code": "OBSERV"}}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_non_multi_group_model_skipped(self):
        rule = RuleDDF00213()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyInterventions": [],
                    "studyDesigns": [
                        {
                            "id": "D1",
                            "studyType": {"code": "C98388"},
                            "model": {"code": "SINGLE_GROUP"},
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_multi_group_with_multiple_interventions_passes(self):
        rule = RuleDDF00213()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyInterventions": [{"id": "I1"}, {"id": "I2"}],
                    "studyDesigns": [
                        {
                            "id": "D1",
                            "studyType": {"code": "C98388"},
                            "model": {"code": "C82637"},
                            "studyInterventionIds": ["I1", "I2"],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_multi_group_with_single_intervention_fails(self):
        rule = RuleDDF00213()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyInterventions": [{"id": "I1"}],
                    "studyDesigns": [
                        {
                            "id": "D1",
                            "studyType": {"code": "C98388"},
                            "model": {"code": "C82637"},
                            "studyInterventionIds": ["I1"],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() >= 1

    def test_non_dict_design_skipped(self):
        rule = RuleDDF00213()
        data = self._data([{"id": "SV1", "studyDesigns": ["bogus"]}])
        assert rule.validate({"data": data}) is True
