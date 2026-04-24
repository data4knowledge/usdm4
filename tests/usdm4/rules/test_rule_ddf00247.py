"""Tests for RuleDDF00247 — Syntax template text valid USDM-XHTML (schema)."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00247 import RuleDDF00247, SCOPE_CLASSES
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00247:
    def test_metadata(self):
        rule = RuleDDF00247()
        assert rule._rule == "DDF00247"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_empty_and_non_string_skipped(self):
        rule = RuleDDF00247()
        data = self._data(
            {
                "Objective": [
                    {"id": "O1", "text": ""},
                    {"id": "O2", "text": "   "},
                    {"id": "O3", "text": None},
                    {"id": "O4"},
                ]
            }
        )
        assert rule.validate({"data": data}) is True

    def test_valid_xhtml_passes(self):
        rule = RuleDDF00247()
        data = self._data({"Endpoint": [{"id": "E1", "text": "<p>Safe content</p>"}]})
        assert rule.validate({"data": data}) is True

    def test_malformed_xml_fails(self):
        rule = RuleDDF00247()
        data = self._data({"Condition": [{"id": "C1", "text": "<p>unclosed"}]})
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_schema_violation_fails(self):
        """<p> directly inside <ul> is well-formed XML but invalid XHTML.

        Regression: previous xml.etree-based impl let it through. The
        INC1/INC3 eligibility texts in sample 2 are of this shape — CORE
        flagged them, d4k missed them until this rewrite.
        """
        rule = RuleDDF00247()
        data = self._data(
            {
                "EligibilityCriterionItem": [
                    {
                        "id": "I1",
                        "text": "<p>intro</p><ul><p>bad</p><li>ok</li></ul>",
                    }
                ]
            }
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_each_scope_class_iterated(self):
        """Bad text under each of the six scope classes must be caught."""
        rule = RuleDDF00247()
        by_klass = {
            klass: [{"id": f"{klass}_1", "text": "<p>unclosed"}]
            for klass in SCOPE_CLASSES
        }
        data = self._data(by_klass)
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == len(SCOPE_CLASSES)

    def test_scope_classes_constant(self):
        assert "Objective" in SCOPE_CLASSES
        assert "Endpoint" in SCOPE_CLASSES
        assert len(SCOPE_CLASSES) == 6
