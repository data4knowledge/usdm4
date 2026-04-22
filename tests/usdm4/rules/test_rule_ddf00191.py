"""Tests for RuleDDF00191 — open-label designs should not have masked roles."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00191 import RuleDDF00191, _blinding_code
from usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# _blinding_code helper
# ---------------------------------------------------------------------------


def test_blinding_code_missing_schema_returns_none():
    assert _blinding_code({}) is None


def test_blinding_code_non_dict_schema_returns_none():
    assert _blinding_code({"blindingSchema": "x"}) is None


def test_blinding_code_schema_without_standard_returns_none():
    assert _blinding_code({"blindingSchema": {"other": 1}}) is None


def test_blinding_code_reads_standard_code():
    assert (
        _blinding_code({"blindingSchema": {"standardCode": {"code": "C49659"}}})
        == "C49659"
    )


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00191:
    def test_metadata(self):
        rule = RuleDDF00191()
        assert rule._rule == "DDF00191"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def _open_label(self, id_):
        return {
            "id": id_,
            "blindingSchema": {"standardCode": {"code": "C49659"}},
        }

    def test_no_open_label_design_skipped(self):
        rule = RuleDDF00191()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [
                        {
                            "id": "D1",
                            "blindingSchema": {"standardCode": {"code": "C15228"}},
                        }
                    ],
                    "roles": [],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_masked_role_applicable_via_design_fails(self):
        rule = RuleDDF00191()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [self._open_label("D1")],
                    "roles": [
                        {
                            "id": "R1",
                            "appliesToIds": ["D1"],
                            "masking": {"isMasked": True},
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_masked_role_applicable_via_version_fails(self):
        rule = RuleDDF00191()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [self._open_label("D1")],
                    "roles": [
                        {
                            "id": "R1",
                            "appliesToIds": ["SV1"],
                            "masking": {"isMasked": True},
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False

    def test_unmasked_role_passes(self):
        rule = RuleDDF00191()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [self._open_label("D1")],
                    "roles": [
                        {
                            "id": "R1",
                            "appliesToIds": ["D1"],
                            "masking": {"isMasked": False},
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_non_applicable_role_is_ignored(self):
        rule = RuleDDF00191()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [self._open_label("D1")],
                    "roles": [
                        {
                            "id": "R1",
                            "appliesToIds": ["OTHER"],
                            "masking": {"isMasked": True},
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_non_dict_role_ignored(self):
        rule = RuleDDF00191()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [self._open_label("D1")],
                    "roles": [None, "scalar"],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_masking_not_dict_skipped(self):
        """masking is not a dict → won't trigger failure even if role applies."""
        rule = RuleDDF00191()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [self._open_label("D1")],
                    "roles": [
                        {
                            "id": "R1",
                            "appliesToIds": ["D1"],
                            "masking": "scalar",
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
