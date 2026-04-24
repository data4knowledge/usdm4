"""Tests for RuleDDF00248 — EligibilityCriterionItem used at most once per SD."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00248 import RuleDDF00248
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00248:
    def test_metadata(self):
        rule = RuleDDF00248()
        assert rule._rule == "DDF00248"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, interventional=None, observational=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: {
            "InterventionalStudyDesign": interventional or [],
            "ObservationalStudyDesign": observational or [],
        }.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_unique_passes(self):
        rule = RuleDDF00248()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "eligibilityCriteria": [
                        {"id": "EC1", "criterionItemId": "I1"},
                        {"id": "EC2", "criterionItemId": "I2"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_empty_item_skipped(self):
        rule = RuleDDF00248()
        data = self._data(
            observational=[
                {
                    "id": "SD1",
                    "eligibilityCriteria": [
                        {"id": "EC1"},
                        {"id": "EC2", "criterionItemId": ""},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00248()
        data = self._data(
            interventional=[
                {
                    "id": "SD1",
                    "eligibilityCriteria": [
                        {"id": "EC1", "criterionItemId": "I1"},
                        {"id": "EC2", "criterionItemId": "I1"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_non_dict_skipped(self):
        rule = RuleDDF00248()
        data = self._data(
            interventional=[
                {"id": "SD1", "eligibilityCriteria": ["bad", {"id": "EC1"}]}
            ]
        )
        assert rule.validate({"data": data}) is True
