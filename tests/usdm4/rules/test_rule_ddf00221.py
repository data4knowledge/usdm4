"""Tests for RuleDDF00221 — distinct therapeuticAreas per StudyDesign."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00221 import RuleDDF00221
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00221:
    def test_metadata(self):
        rule = RuleDDF00221()
        assert rule._rule == "DDF00221"
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
        rule = RuleDDF00221()
        data = self._data(interventional=[{"id": "D1"}])
        assert rule.validate({"data": data}) is True

    def test_distinct_passes(self):
        rule = RuleDDF00221()
        data = self._data(
            interventional=[
                {
                    "id": "D1",
                    "therapeuticAreas": [
                        {"codeSystem": "X", "codeSystemVersion": "1", "code": "A"},
                        {"codeSystem": "X", "codeSystemVersion": "1", "code": "B"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00221()
        data = self._data(
            observational=[
                {
                    "id": "D1",
                    "therapeuticAreas": [
                        {"codeSystem": "X", "codeSystemVersion": "1", "code": "A"},
                        {"codeSystem": "X", "codeSystemVersion": "1", "code": "A"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "duplicate entry" in rule.errors().dump()

    def test_missing_code_ignored(self):
        rule = RuleDDF00221()
        data = self._data(
            interventional=[
                {
                    "id": "D1",
                    "therapeuticAreas": [
                        {"codeSystem": "X", "codeSystemVersion": "1"},
                        "bogus",
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
