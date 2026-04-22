"""Tests for RuleDDF00084 — exactly one Primary Objective per study design."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00084 import RuleDDF00084
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00084:
    def test_metadata(self):
        rule = RuleDDF00084()
        assert rule._rule == "DDF00084"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, interventional=None, observational=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "InterventionalStudyDesign": interventional or [],
            "ObservationalStudyDesign": observational or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_exactly_one_primary_passes(self):
        rule = RuleDDF00084()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "objectives": [
                        {"id": "O1", "level": {"code": "C94496"}},
                        {"id": "O2", "level": {"code": "OTHER"}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_no_primary_fails(self):
        rule = RuleDDF00084()
        data = self._data(
            observational=[
                {
                    "id": "SD1",
                    "objectives": [{"id": "O1", "level": {"code": "OTHER"}}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_two_primaries_fail(self):
        rule = RuleDDF00084()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "objectives": [
                        {"id": "O1", "level": {"code": "C94496"}},
                        {"id": "O2", "level": {"code": "C94496"}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False

    def test_empty_objectives_fail(self):
        rule = RuleDDF00084()
        data = self._data(interventional=[{"id": "SD1"}])
        assert rule.validate({"data": data}) is False

    def test_non_dict_level_counted_as_zero(self):
        rule = RuleDDF00084()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "objectives": [{"id": "O1", "level": "bad"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
