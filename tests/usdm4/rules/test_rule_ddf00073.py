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
                    {"id": "C1", "codeSystem": "X", "codeSystemVersion": "1"}
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

    def test_multiple_versions_emit_one_failure_per_version(self):
        """One failure per (codeSystem, codeSystemVersion) group, not per Code.

        With 2 versions in use (one used by 1 code, another by 1 code), we
        expect exactly 2 failures — matching CORE-000808's granularity.
        """
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

    def test_many_codes_still_collapse_to_one_per_version(self):
        """20 codes split 15/5 across two versions should yield 2 failures."""
        rule = RuleDDF00073()
        codes = []
        parents = {}
        for i in range(15):
            cid = f"C{i}"
            codes.append({"id": cid, "codeSystem": "X", "codeSystemVersion": "1"})
            parents[cid] = {"id": "SV1"}
        for i in range(15, 20):
            cid = f"C{i}"
            codes.append({"id": cid, "codeSystem": "X", "codeSystemVersion": "2"})
            parents[cid] = {"id": "SV1"}
        data = self._data(
            {"StudyVersion": [{"id": "SV1"}], "Code": codes},
            parent_map=parents,
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
        dump = rule.errors().dump(level=RuleTemplate.WARNING)
        # The count-of-codes per version should appear in the message.
        assert "15 Code(s)" in dump
        assert "5 Code(s)" in dump

    def test_three_versions_yield_three_failures(self):
        rule = RuleDDF00073()
        data = self._data(
            {
                "StudyVersion": [{"id": "SV1"}],
                "Code": [
                    {"id": "C1", "codeSystem": "X", "codeSystemVersion": "1"},
                    {"id": "C2", "codeSystem": "X", "codeSystemVersion": "2"},
                    {"id": "C3", "codeSystem": "X", "codeSystemVersion": "3"},
                ],
            },
            parent_map={
                "C1": {"id": "SV1"},
                "C2": {"id": "SV1"},
                "C3": {"id": "SV1"},
            },
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 3

    def test_different_code_systems_independent(self):
        """Version spread per codeSystem — different systems shouldn't cross-pollute."""
        rule = RuleDDF00073()
        data = self._data(
            {
                "StudyVersion": [{"id": "SV1"}],
                "Code": [
                    {"id": "C1", "codeSystem": "X", "codeSystemVersion": "1"},
                    {"id": "C2", "codeSystem": "X", "codeSystemVersion": "2"},
                    {"id": "C3", "codeSystem": "Y", "codeSystemVersion": "1"},
                ],
            },
            parent_map={
                "C1": {"id": "SV1"},
                "C2": {"id": "SV1"},
                "C3": {"id": "SV1"},
            },
        )
        assert rule.validate({"data": data}) is False
        # X has 2 versions (2 failures); Y has 1 version (0 failures)
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
