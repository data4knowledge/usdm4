"""Tests for RuleDDF00035 — Code 1:1 mapping code↔decode per (codeSystem, codeSystemVersion)."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00035 import RuleDDF00035
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00035:
    def test_metadata(self):
        rule = RuleDDF00035()
        assert rule._rule == "DDF00035"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, codes):
        data = MagicMock()
        data.instances_by_klass.return_value = codes
        data.path_by_id.return_value = "$.path"
        return data

    def test_missing_attribute_skipped(self):
        rule = RuleDDF00035()
        data = self._data([{"id": "C1", "codeSystem": "X", "code": "A"}])
        assert rule.validate({"data": data}) is True

    def test_unique_pairs_pass(self):
        rule = RuleDDF00035()
        data = self._data(
            [
                {
                    "id": "C1",
                    "codeSystem": "X",
                    "codeSystemVersion": "1",
                    "code": "A",
                    "decode": "Apple",
                },
                {
                    "id": "C2",
                    "codeSystem": "X",
                    "codeSystemVersion": "1",
                    "code": "B",
                    "decode": "Banana",
                },
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_code_with_multiple_decodes_fails(self):
        rule = RuleDDF00035()
        data = self._data(
            [
                {
                    "id": "C1",
                    "codeSystem": "X",
                    "codeSystemVersion": "1",
                    "code": "A",
                    "decode": "Apple",
                },
                {
                    "id": "C2",
                    "codeSystem": "X",
                    "codeSystemVersion": "1",
                    "code": "A",
                    "decode": "Avocado",
                },
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2

    def test_decode_with_multiple_codes_fails(self):
        rule = RuleDDF00035()
        data = self._data(
            [
                {
                    "id": "C1",
                    "codeSystem": "X",
                    "codeSystemVersion": "1",
                    "code": "A",
                    "decode": "Apple",
                },
                {
                    "id": "C2",
                    "codeSystem": "X",
                    "codeSystemVersion": "1",
                    "code": "B",
                    "decode": "Apple",
                },
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
