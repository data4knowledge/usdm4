"""Tests for RuleDDF00012 — exactly one mainTimeline per study design."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00012 import RuleDDF00012
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00012:
    def test_metadata(self):
        rule = RuleDDF00012()
        assert rule._rule == "DDF00012"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, study_design=None, interventional=None, observational=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "StudyDesign": study_design or [],
            "InterventionalStudyDesign": interventional or [],
            "ObservationalStudyDesign": observational or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_one_main_passes(self):
        rule = RuleDDF00012()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "scheduleTimelines": [
                        {"id": "T1", "mainTimeline": True},
                        {"id": "T2", "mainTimeline": False},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_zero_main_fails(self):
        rule = RuleDDF00012()
        data = self._data(observational=[{"id": "SD1", "scheduleTimelines": []}])
        assert rule.validate({"data": data}) is False

    def test_two_mains_fail(self):
        rule = RuleDDF00012()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "scheduleTimelines": [
                        {"id": "T1", "mainTimeline": True},
                        {"id": "T2", "mainTimeline": True},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False

    def test_base_study_design_iterated(self):
        """USDM V4 uses 'StudyDesign' as a concrete type alongside its two
        subclasses. The rule must iterate all three."""
        rule = RuleDDF00012()
        data = self._data(
            study_design=[
                {
                    "id": "SD1",
                    "scheduleTimelines": [
                        {"id": "T1", "mainTimeline": True},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_base_study_design_zero_main_fails(self):
        rule = RuleDDF00012()
        data = self._data(
            study_design=[{"id": "SD1", "scheduleTimelines": []}]
        )
        assert rule.validate({"data": data}) is False
