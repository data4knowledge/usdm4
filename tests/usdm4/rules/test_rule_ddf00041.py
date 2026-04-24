"""Tests for RuleDDF00041 — at least one Primary Endpoint per study design."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00041 import RuleDDF00041
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00041:
    def test_metadata(self):
        rule = RuleDDF00041()
        assert rule._rule == "DDF00041"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, interventional=None, observational=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "InterventionalStudyDesign": interventional or [],
            "ObservationalStudyDesign": observational or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_primary_endpoint_present_passes(self):
        rule = RuleDDF00041()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "objectives": [
                        {
                            "id": "O1",
                            "endpoints": [
                                {"id": "E1", "level": {"code": "C94496"}},
                                {"id": "E2", "level": {"code": "OTHER"}},
                            ],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_no_primary_endpoint_fails(self):
        rule = RuleDDF00041()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "objectives": [
                        {
                            "id": "O1",
                            "endpoints": [
                                {"id": "E1", "level": {"code": "OTHER"}}
                            ],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_empty_objectives_fail(self):
        rule = RuleDDF00041()
        data = self._data(observational=[{"id": "SD1"}])
        assert rule.validate({"data": data}) is False

    def test_endpoints_across_multiple_objectives(self):
        rule = RuleDDF00041()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "objectives": [
                        {
                            "id": "O1",
                            "endpoints": [{"id": "E1", "level": {"code": "OTHER"}}],
                        },
                        {
                            "id": "O2",
                            "endpoints": [{"id": "E2", "level": {"code": "C94496"}}],
                        },
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_non_dict_level_ignored(self):
        rule = RuleDDF00041()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "objectives": [
                        {
                            "id": "O1",
                            "endpoints": [{"id": "E1", "level": "bad"}],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False

    def test_no_study_designs_passes_vacuously(self):
        rule = RuleDDF00041()
        data = self._data()
        assert rule.validate({"data": data}) is True
