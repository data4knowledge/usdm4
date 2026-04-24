"""Tests for RuleDDF00155 — CDISC Code.codeSystemVersion must be a valid release."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00155 import RuleDDF00155
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00155:
    def test_metadata(self):
        rule = RuleDDF00155()
        assert rule._rule == "DDF00155"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, codes):
        data = MagicMock()
        data.instances_by_klass.return_value = codes
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_cdisc_skipped(self):
        rule = RuleDDF00155()
        data = self._data(
            [{"id": "C1", "codeSystem": "http://other.org", "codeSystemVersion": "x"}]
        )
        assert rule.validate({"data": data}) is True

    def test_valid_version_passes(self):
        rule = RuleDDF00155()
        data = self._data(
            [
                {
                    "id": "C1",
                    "codeSystem": "http://www.cdisc.org",
                    "codeSystemVersion": "2025-03-28",
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_missing_version_fails(self):
        rule = RuleDDF00155()
        data = self._data([{"id": "C1", "codeSystem": "http://www.cdisc.org"}])
        assert rule.validate({"data": data}) is False
        assert "Missing" in rule.errors().dump()

    def test_invalid_version_fails(self):
        rule = RuleDDF00155()
        data = self._data(
            [
                {
                    "id": "C1",
                    "codeSystem": "http://www.cdisc.org",
                    "codeSystemVersion": "1999-01-01",
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "Invalid" in rule.errors().dump()
