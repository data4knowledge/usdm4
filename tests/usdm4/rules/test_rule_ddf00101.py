"""Tests for RuleDDF00101 — Interventional design must link a Procedure to a StudyIntervention."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00101 import (
    INTERVENTIONAL_CODE,
    RuleDDF00101,
    _is_interventional,
)
from usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# _is_interventional helper
# ---------------------------------------------------------------------------


def test_is_interventional_missing_type():
    assert _is_interventional({}) is False


def test_is_interventional_non_dict_type():
    assert _is_interventional({"studyType": "C98388"}) is False


def test_is_interventional_wrong_code():
    assert _is_interventional({"studyType": {"code": "OTHER"}}) is False


def test_is_interventional_matches():
    assert _is_interventional({"studyType": {"code": INTERVENTIONAL_CODE}}) is True


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00101:
    def test_metadata(self):
        rule = RuleDDF00101()
        assert rule._rule == "DDF00101"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_interventional_design_skipped(self):
        rule = RuleDDF00101()
        data = self._data(
            {
                "InterventionalStudyDesign": [
                    {"id": "SD1", "studyType": {"code": "OTHER"}}
                ]
            }
        )
        assert rule.validate({"data": data}) is True

    def test_interventional_with_linked_procedure_passes(self):
        rule = RuleDDF00101()
        data = self._data(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "SD1",
                        "studyType": {"code": INTERVENTIONAL_CODE},
                        "activities": [
                            {
                                "id": "ACT1",
                                "definedProcedures": [
                                    {"id": "P1", "studyInterventionId": "SI1"}
                                ],
                            }
                        ],
                    }
                ]
            }
        )
        assert rule.validate({"data": data}) is True

    def test_interventional_no_activities_fails(self):
        rule = RuleDDF00101()
        data = self._data(
            {
                "InterventionalStudyDesign": [
                    {"id": "SD1", "studyType": {"code": INTERVENTIONAL_CODE}}
                ]
            }
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_interventional_non_dict_activity_skipped(self):
        """Non-dict activities are skipped; since no other activities link,
        the design still fails."""
        rule = RuleDDF00101()
        data = self._data(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "SD1",
                        "studyType": {"code": INTERVENTIONAL_CODE},
                        "activities": ["bogus", None],
                    }
                ]
            }
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_interventional_procedure_without_study_intervention_fails(self):
        rule = RuleDDF00101()
        data = self._data(
            {
                "InterventionalStudyDesign": [
                    {
                        "id": "SD1",
                        "studyType": {"code": INTERVENTIONAL_CODE},
                        "activities": [
                            {
                                "id": "ACT1",
                                "definedProcedures": [
                                    {"id": "P1"},  # no studyInterventionId
                                    "bogus",  # non-dict procedure skipped
                                ],
                            }
                        ],
                    }
                ]
            }
        )
        assert rule.validate({"data": data}) is False

    def test_observational_with_interventional_type_also_checked(self):
        """The rule iterates both klasses; an ObservationalStudyDesign flagged
        as interventional is still checked."""
        rule = RuleDDF00101()
        data = self._data(
            {
                "ObservationalStudyDesign": [
                    {
                        "id": "SD2",
                        "studyType": {"code": INTERVENTIONAL_CODE},
                        "activities": [
                            {
                                "id": "ACT1",
                                "definedProcedures": [
                                    {"id": "P1", "studyInterventionId": "SI1"}
                                ],
                            }
                        ],
                    }
                ]
            }
        )
        assert rule.validate({"data": data}) is True
