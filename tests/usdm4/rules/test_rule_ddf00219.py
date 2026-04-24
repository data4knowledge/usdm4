"""Tests for RuleDDF00219 — StudyDesign.characteristics distinct by code."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00219 import RuleDDF00219
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00219:
    def test_metadata(self):
        rule = RuleDDF00219()
        assert rule._rule == "DDF00219"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, interventional=None, observational=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "InterventionalStudyDesign": interventional or [],
            "ObservationalStudyDesign": observational or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_empty_passes(self):
        rule = RuleDDF00219()
        data = self._data(interventional=[{"id": "SD1"}])
        assert rule.validate({"data": data}) is True

    def test_distinct_passes(self):
        rule = RuleDDF00219()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "characteristics": [{"code": "C1"}, {"code": "C2"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00219()
        data = self._data(
            observational=[
                {
                    "id": "SD1",
                    "characteristics": [{"code": "C1"}, {"code": "C1"}, {"code": "C2"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "duplicate code(s): C1" in rule.errors().dump()
