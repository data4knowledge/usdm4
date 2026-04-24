"""Tests for RuleDDF00222 — StudyDesign.intentTypes distinct by code."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00222 import RuleDDF00222
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00222:
    def test_metadata(self):
        rule = RuleDDF00222()
        assert rule._rule == "DDF00222"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, interventional=None, observational=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "InterventionalStudyDesign": interventional or [],
            "ObservationalStudyDesign": observational or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_distinct_passes(self):
        rule = RuleDDF00222()
        data = self._data(
            interventional=[
                {"id": "SD1", "intentTypes": [{"code": "T1"}, {"code": "T2"}]}
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00222()
        data = self._data(
            observational=[
                {"id": "SD1", "intentTypes": [{"code": "T1"}, {"code": "T1"}]}
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "duplicate code(s): T1" in rule.errors().dump()
