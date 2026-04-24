"""Tests for RuleDDF00187 — NarrativeContentItem.text valid USDM-XHTML (schema)."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00187 import RuleDDF00187
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00187:
    def test_metadata(self):
        rule = RuleDDF00187()
        assert rule._rule == "DDF00187"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, items):
        data = MagicMock()
        data.instances_by_klass.return_value = items
        data.path_by_id.return_value = "$.path"
        return data

    def test_empty_and_missing_skipped(self):
        rule = RuleDDF00187()
        data = self._data(
            [
                {"id": "N1", "text": ""},
                {"id": "N2", "text": "  "},
                {"id": "N3", "text": None},
                {"id": "N4"},
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_valid_xhtml_passes(self):
        rule = RuleDDF00187()
        data = self._data([{"id": "N1", "text": "<p>Valid</p>"}])
        assert rule.validate({"data": data}) is True

    def test_malformed_xml_fails(self):
        rule = RuleDDF00187()
        data = self._data([{"id": "N1", "text": "<p>unclosed"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_schema_violation_fails(self):
        """Well-formed XML but invalid USDM-XHTML — <p> directly inside <ul>.

        Regression: the previous xml.etree-based implementation only
        checked well-formedness and let this through. CORE-001069 flags
        it as an XHTML schema violation, and d4k now matches.
        """
        rule = RuleDDF00187()
        data = self._data(
            [{"id": "N1", "text": "<ul><p>should be li</p><li>ok</li></ul>"}]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_usdm_ref_extension_is_allowed(self):
        rule = RuleDDF00187()
        data = self._data(
            [
                {
                    "id": "N1",
                    "text": '<p>See <usdm:ref klass="X" id="Y" attribute="name"/></p>',
                }
            ]
        )
        assert rule.validate({"data": data}) is True
