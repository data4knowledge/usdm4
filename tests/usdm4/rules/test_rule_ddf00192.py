"""Tests for RuleDDF00192 — double-blind designs need ≥2 masked StudyRoles."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00192 import RuleDDF00192, _blinding_code
from usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# _blinding_code helper
# ---------------------------------------------------------------------------


def test_blinding_code_missing_schema_returns_none():
    assert _blinding_code({"blindingSchema": None}) is None
    assert _blinding_code({}) is None


def test_blinding_code_schema_without_standard_returns_none():
    assert _blinding_code({"blindingSchema": {"other": 1}}) is None


def test_blinding_code_reads_standard_code():
    design = {"blindingSchema": {"standardCode": {"code": "C15228"}}}
    assert _blinding_code(design) == "C15228"


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00192:
    def test_metadata(self):
        rule = RuleDDF00192()
        assert rule._rule == "DDF00192"
        assert rule._level == RuleTemplate.WARNING
        assert (
            rule._rule_text
            == "A masking is expected to be defined for at least two study roles in a study design with a double blind blinding schema."
        )

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def _design(self, id_, double_blind=True):
        code = "C15228" if double_blind else "C15229"
        return {
            "id": id_,
            "blindingSchema": {"standardCode": {"code": code}},
        }

    def _role(self, applies_to_ids, masked):
        return {
            "id": "R",
            "appliesToIds": applies_to_ids,
            "masking": {"isMasked": masked},
        }

    def test_non_double_blind_is_skipped(self):
        rule = RuleDDF00192()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [self._design("D1", double_blind=False)],
                    "roles": [],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_non_dict_design_is_skipped(self):
        rule = RuleDDF00192()
        data = self._data(
            [{"id": "SV1", "studyDesigns": ["scalar", None], "roles": []}]
        )
        assert rule.validate({"data": data}) is True

    def test_zero_masked_roles_fails(self):
        rule = RuleDDF00192()
        design = self._design("D1")
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [design],
                    "roles": [],  # no roles at all
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_one_masked_role_fails(self):
        """Only 1 role that applies to the design is masked → failure."""
        rule = RuleDDF00192()
        design = self._design("D1")
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [design],
                    "roles": [
                        self._role(["D1"], masked=True),
                        self._role(["D1"], masked=False),
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_two_masked_roles_via_design_id_passes(self):
        rule = RuleDDF00192()
        design = self._design("D1")
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [design],
                    "roles": [
                        self._role(["D1"], masked=True),
                        self._role(["D1"], masked=True),
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_two_masked_roles_via_version_id_passes(self):
        """Roles with appliesToIds containing the StudyVersion id also count."""
        rule = RuleDDF00192()
        design = self._design("D1")
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [design],
                    "roles": [
                        self._role(["SV1"], masked=True),
                        self._role(["SV1"], masked=True),
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_non_applicable_roles_are_ignored(self):
        """Role whose appliesToIds don't match SV or design → excluded from count."""
        rule = RuleDDF00192()
        design = self._design("D1")
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [design],
                    "roles": [
                        self._role(["D1"], masked=True),
                        self._role(["OTHER"], masked=True),  # non-applicable
                    ],
                }
            ]
        )
        # Only one applicable masked role → failure.
        assert rule.validate({"data": data}) is False

    def test_non_dict_role_is_skipped(self):
        rule = RuleDDF00192()
        design = self._design("D1")
        data = self._data(
            [
                {
                    "id": "SV1",
                    "studyDesigns": [design],
                    "roles": [
                        None,
                        "scalar",
                        self._role(["D1"], masked=True),
                        self._role(["D1"], masked=True),
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
