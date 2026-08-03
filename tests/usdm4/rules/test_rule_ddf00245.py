"""Tests for RuleDDF00245 — NarrativeContent.sectionNumber unique per SDDV."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00245 import RuleDDF00245
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00245:
    def test_metadata(self):
        rule = RuleDDF00245()
        assert rule._rule == "DDF00245"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, sddvs):
        data = MagicMock()
        data.instances_by_klass.return_value = sddvs
        data.path_by_id.return_value = "$.path"
        return data

    def test_unique_passes(self):
        rule = RuleDDF00245()
        data = self._data(
            [
                {
                    "id": "SDDV1",
                    "contents": [
                        {"id": "N1", "sectionNumber": "1"},
                        {"id": "N2", "sectionNumber": "2"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_empty_section_number_skipped(self):
        rule = RuleDDF00245()
        data = self._data(
            [
                {
                    "id": "SDDV1",
                    "contents": [
                        {"id": "N1", "sectionNumber": ""},
                        {"id": "N2", "sectionNumber": None},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00245()
        data = self._data(
            [
                {
                    "id": "SDDV1",
                    "contents": [
                        {"id": "N1", "sectionNumber": "1"},
                        {"id": "N2", "sectionNumber": "1"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2

    def test_non_dict_skipped(self):
        rule = RuleDDF00245()
        data = self._data(
            [{"id": "SDDV1", "contents": ["bad", {"id": "N1", "sectionNumber": "1"}]}]
        )
        assert rule.validate({"data": data}) is True
