"""Tests for RuleDDF00189 — StudyRole.appliesToIds exclusively version OR designs."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00189 import RuleDDF00189
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00189:
    def test_metadata(self):
        rule = RuleDDF00189()
        assert rule._rule == "DDF00189"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def test_role_refs_version_passes(self):
        rule = RuleDDF00189()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [{"id": "SD1"}],
                    "roles": [{"id": "R1", "appliesToIds": ["SV1"]}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_role_refs_designs_passes(self):
        rule = RuleDDF00189()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [{"id": "SD1"}, {"id": "SD2"}],
                    "roles": [{"id": "R1", "appliesToIds": ["SD1", "SD2"]}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_role_refs_empty_fails(self):
        rule = RuleDDF00189()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [],
                    "roles": [{"id": "R1", "appliesToIds": []}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False

    def test_role_refs_mixed_fails(self):
        rule = RuleDDF00189()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [{"id": "SD1"}],
                    "roles": [{"id": "R1", "appliesToIds": ["SV1", "SD1"]}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False

    def test_non_dict_role_skipped(self):
        rule = RuleDDF00189()
        data = self._data([{"id": "SV1", "studyDesigns": [], "roles": ["bad"]}])
        assert rule.validate({"data": data}) is True
