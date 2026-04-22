"""Tests for RuleDDF00073 — single codeSystemVersion per codeSystem per StudyVersion."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00073 import RuleDDF00073
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00073:
    def test_metadata(self):
        rule = RuleDDF00073()
        assert rule._rule == "DDF00073"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, by_klass, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda cid, _k: (parent_map or {}).get(cid)
        return data

    def test_code_not_in_scope_skipped(self):
        rule = RuleDDF00073()
        data = self._data(
            {
                "StudyVersion": [{"id": "SV1"}],
                "Code": [
                    {
                        "id": "C1",
                        "codeSystem": "X",
                        "codeSystemVersion": "1",
                    }
                ],
            },
            parent_map={"C1": None},
        )
        assert rule.validate({"data": data}) is True

    def test_unique_version_passes(self):
        rule = RuleDDF00073()
        data = self._data(
            {
                "StudyVersion": [{"id": "SV1"}],
                "Code": [
                    {"id": "C1", "codeSystem": "X", "codeSystemVersion": "1"},
                    {"id": "C2", "codeSystem": "X", "codeSystemVersion": "1"},
                ],
            },
            parent_map={"C1": {"id": "SV1"}, "C2": {"id": "SV1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_multiple_versions_fail(self):
        rule = RuleDDF00073()
        data = self._data(
            {
                "StudyVersion": [{"id": "SV1"}],
                "Code": [
                    {"id": "C1", "codeSystem": "X", "codeSystemVersion": "1"},
                    {"id": "C2", "codeSystem": "X", "codeSystemVersion": "2"},
                ],
            },
            parent_map={"C1": {"id": "SV1"}, "C2": {"id": "SV1"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2

    def test_missing_cs_csv_skipped(self):
        rule = RuleDDF00073()
        data = self._data(
            {
                "StudyVersion": [{"id": "SV1"}],
                "Code": [{"id": "C1", "codeSystem": None, "codeSystemVersion": None}],
            },
            parent_map={"C1": {"id": "SV1"}},
        )
        assert rule.validate({"data": data}) is True
