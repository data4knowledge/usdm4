"""Tests for RuleDDF00198 — SDDV must be referenced by a StudyVersion or StudyDesign."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00198 import RuleDDF00198
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00198:
    def test_metadata(self):
        rule = RuleDDF00198()
        assert rule._rule == "DDF00198"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_referenced_by_version_passes(self):
        rule = RuleDDF00198()
        data = self._data(
            {
                "StudyVersion": [{"id": "SV1", "documentVersionIds": ["DV1"]}],
                "StudyDefinitionDocumentVersion": [{"id": "DV1"}],
            }
        )
        assert rule.validate({"data": data}) is True

    def test_referenced_by_design_passes(self):
        rule = RuleDDF00198()
        data = self._data(
            {
                "InterventionalStudyDesign": [
                    {"id": "SD1", "documentVersionIds": ["DV1"]}
                ],
                "StudyDefinitionDocumentVersion": [{"id": "DV1"}],
            }
        )
        assert rule.validate({"data": data}) is True

    def test_unreferenced_fails(self):
        rule = RuleDDF00198()
        data = self._data({"StudyDefinitionDocumentVersion": [{"id": "DV1"}]})
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
