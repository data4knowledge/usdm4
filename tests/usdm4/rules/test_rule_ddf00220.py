"""Tests for RuleDDF00220 — StudyDesign.subTypes distinct by code."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00220 import RuleDDF00220
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00220:
    def test_metadata(self):
        rule = RuleDDF00220()
        assert rule._rule == "DDF00220"
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
        rule = RuleDDF00220()
        data = self._data(
            interventional=[{"id": "SD1", "subTypes": [{"code": "A"}, {"code": "B"}]}]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00220()
        data = self._data(
            observational=[{"id": "SD1", "subTypes": [{"code": "A"}, {"code": "A"}]}]
        )
        assert rule.validate({"data": data}) is False
        assert "duplicate code(s): A" in rule.errors().dump()

    def test_non_dict_skipped(self):
        rule = RuleDDF00220()
        data = self._data(
            interventional=[{"id": "SD1", "subTypes": ["bad", {"code": "A"}]}]
        )
        assert rule.validate({"data": data}) is True
