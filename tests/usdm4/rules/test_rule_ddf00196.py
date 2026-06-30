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

    def test_distinct_unnumbered_sections_pass(self):
        # Title Page and Amendment Details (C217272) both carry an empty
        # sectionNumber. They are genuinely different sections, so they
        # must not collide on "" and trip the one-to-one check.
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
                                    "sectionNumber": "",
                                    "sectionTitle": "Title Page",
                                },
                                {
                                    "id": "R2",
                                    "appliesToId": "D1",
                                    "sectionNumber": "",
                                    "sectionTitle": "Amendment Details",
                                },
                            ]
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_repeated_same_unnumbered_section_passes(self):
        # The same unnumbered section referenced by two changes is fine.
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
                                    "sectionNumber": "",
                                    "sectionTitle": "Title Page",
                                },
                                {
                                    "id": "R2",
                                    "appliesToId": "D1",
                                    "sectionNumber": "",
                                    "sectionTitle": "Title Page",
                                },
                            ]
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_numbered_inconsistency_still_fails_alongside_unnumbered(self):
        # The empty-number exemption must not mask a real number↔title
        # clash on a genuinely numbered section in the same amendment.
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
                                    "sectionNumber": "",
                                    "sectionTitle": "Title Page",
                                },
                                {
                                    "id": "R2",
                                    "appliesToId": "D1",
                                    "sectionNumber": "5",
                                    "sectionTitle": "Trial Population",
                                },
                                {
                                    "id": "R3",
                                    "appliesToId": "D1",
                                    "sectionNumber": "5",
                                    "sectionTitle": "Something Else",
                                },
                            ]
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        # Only the two clashing numbered refs are reported, not the named one.
        assert rule.errors().count() == 2
