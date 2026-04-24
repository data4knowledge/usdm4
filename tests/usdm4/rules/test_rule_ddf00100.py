"""Tests for RuleDDF00100 — StudyVersion.titles type uniqueness."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00100 import RuleDDF00100
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00100:
    def test_metadata(self):
        rule = RuleDDF00100()
        assert rule._rule == "DDF00100"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_unique_types_passes(self):
        rule = RuleDDF00100()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "titles": [
                        {"type.code": "C1"},
                        {"type.code": "C2"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_types_fails(self):
        rule = RuleDDF00100()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "titles": [
                        {"type.code": "C1"},
                        {"type.code": "C1"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "Duplicate titles" in rule.errors().dump()

    def test_none_and_empty_filtered(self):
        rule = RuleDDF00100()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "titles": [
                        {"type.code": None},
                        {"type.code": ""},
                        {"type.code": "C1"},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
