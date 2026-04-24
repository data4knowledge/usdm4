"""Tests for RuleDDF00196 — section number ↔ section title 1:1 per amendment."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00196 import RuleDDF00196
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00196:
    def test_metadata(self):
        rule = RuleDDF00196()
        assert rule._rule == "DDF00196"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, amendments):
        data = MagicMock()
        data.instances_by_klass.return_value = amendments
        data.path_by_id.return_value = "$.path"
        return data

    def test_empty_amendment_passes(self):
        rule = RuleDDF00196()
        data = self._data([{"id": "A1"}])
        assert rule.validate({"data": data}) is True

    def test_non_dict_change_skipped(self):
        rule = RuleDDF00196()
        data = self._data([{"id": "A1", "changes": ["bogus"]}])
        assert rule.validate({"data": data}) is True

    def test_consistent_pairs_pass(self):
        rule = RuleDDF00196()
        data = self._data(
            [
                {
                    "id": "A1",
                    "changes": [
                        {
                            "changedSections": [
                                {
                                    "id": "R1",
                                    "appliesToId": "D1",
                                    "sectionNumber": "1",
                                    "sectionTitle": "Intro",
                                },
                                {
                                    "id": "R2",
                                    "appliesToId": "D1",
                                    "sectionNumber": "1",
                                    "sectionTitle": "Intro",
                                },
                            ]
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_same_number_different_titles_fails(self):
        rule = RuleDDF00196()
        data = self._data(
            [
                {
                    "id": "A1",
                    "changes": [
                        {
                            "changedSections": [
                                {
                                    "id": "R1",
                                    "appliesToId": "D1",
                                    "sectionNumber": "1",
                                    "sectionTitle": "Intro",
                                },
                                {
                                    "id": "R2",
                                    "appliesToId": "D1",
                                    "sectionNumber": "1",
                                    "sectionTitle": "Outro",
                                },
                            ]
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2

    def test_same_title_different_numbers_fails(self):
        rule = RuleDDF00196()
        data = self._data(
            [
                {
                    "id": "A1",
                    "changes": [
                        {
                            "changedSections": [
                                {
                                    "id": "R1",
                                    "appliesToId": "D1",
                                    "sectionNumber": "1",
                                    "sectionTitle": "Intro",
                                },
                                {
                                    "id": "R2",
                                    "appliesToId": "D1",
                                    "sectionNumber": "2",
                                    "sectionTitle": "Intro",
                                },
                            ]
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
