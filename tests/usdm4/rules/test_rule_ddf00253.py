"""Tests for RuleDDF00253 — reference substance must not itself reference another substance."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00253 import RuleDDF00253
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00253:
    def test_metadata(self):
        rule = RuleDDF00253()
        assert rule._rule == "DDF00253"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, substances):
        data = MagicMock()
        data.instances_by_klass.return_value = substances
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_substances_passes(self):
        rule = RuleDDF00253()
        data = self._data([])
        assert rule.validate({"data": data}) is True

    def test_no_reference_chain_passes(self):
        """S1 references S2, S2 has no ref — legal."""
        rule = RuleDDF00253()
        data = self._data(
            [
                {"id": "S1", "referenceSubstanceId": "S2"},
                {"id": "S2"},
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_chain_of_references_fails(self):
        """S1→S2→S3 — S2 is both a reference-substance and has its own ref."""
        rule = RuleDDF00253()
        data = self._data(
            [
                {"id": "S1", "referenceSubstanceId": "S2"},
                {"id": "S2", "referenceSubstanceId": "S3"},
                {"id": "S3"},
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
