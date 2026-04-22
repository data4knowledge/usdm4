"""Tests for RuleDDF00063 — standardCodeAlias must not equal standardCode."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00063 import RuleDDF00063
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00063:
    def test_metadata(self):
        rule = RuleDDF00063()
        assert rule._rule == "DDF00063"
        assert rule._level == RuleTemplate.WARNING
        assert (
            rule._rule_text
            == "A standard code alias is not expected to be equal to the standard code (e.g. no equal code or decode for the same coding system version is expected)."
        )

    def _data(self, aliases):
        data = MagicMock()
        data.instances_by_klass.return_value = aliases
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_aliases_is_ignored(self):
        rule = RuleDDF00063()
        data = self._data(
            [
                {
                    "id": "A1",
                    "standardCode": {
                        "codeSystem": "CT",
                        "codeSystemVersion": "1",
                        "code": "X",
                    },
                    # no standardCodeAliases key
                }
            ]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_standard_code_not_a_dict_skips(self):
        rule = RuleDDF00063()
        data = self._data(
            [{"id": "A1", "standardCode": "scalar", "standardCodeAliases": [{}]}]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_different_system_does_not_flag(self):
        rule = RuleDDF00063()
        data = self._data(
            [
                {
                    "id": "A1",
                    "standardCode": {
                        "codeSystem": "CT",
                        "codeSystemVersion": "1",
                        "code": "X",
                    },
                    "standardCodeAliases": [
                        {
                            "codeSystem": "OTHER",
                            "codeSystemVersion": "1",
                            "code": "X",
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_same_system_different_version_does_not_flag(self):
        rule = RuleDDF00063()
        data = self._data(
            [
                {
                    "id": "A1",
                    "standardCode": {
                        "codeSystem": "CT",
                        "codeSystemVersion": "1",
                        "code": "X",
                    },
                    "standardCodeAliases": [
                        {
                            "codeSystem": "CT",
                            "codeSystemVersion": "2",
                            "code": "X",
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_same_code_flags_failure(self):
        """Alias shares system/version and code with standard → failure."""
        rule = RuleDDF00063()
        data = self._data(
            [
                {
                    "id": "A1",
                    "standardCode": {
                        "codeSystem": "CT",
                        "codeSystemVersion": "1",
                        "code": "X",
                        "decode": "Ex",
                    },
                    "standardCodeAliases": [
                        {
                            "codeSystem": "CT",
                            "codeSystemVersion": "1",
                            "code": "X",
                            "decode": "Other",
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_same_decode_case_insensitive_flags_failure(self):
        """Decodes matching case-insensitively on same system → failure."""
        rule = RuleDDF00063()
        data = self._data(
            [
                {
                    "id": "A1",
                    "standardCode": {
                        "codeSystem": "CT",
                        "codeSystemVersion": "1",
                        "code": "X",
                        "decode": "Example",
                    },
                    "standardCodeAliases": [
                        {
                            "codeSystem": "ct",  # case-insensitive match
                            "codeSystemVersion": "1",
                            "code": "Y",
                            "decode": "EXAMPLE",  # case-insensitive match on decode
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_non_dict_alias_is_skipped(self):
        """Scalar/None aliases are silently skipped (the `not isinstance(alias, dict)` continue)."""
        rule = RuleDDF00063()
        data = self._data(
            [
                {
                    "id": "A1",
                    "standardCode": {
                        "codeSystem": "CT",
                        "codeSystemVersion": "1",
                        "code": "X",
                    },
                    "standardCodeAliases": ["scalar", None],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_multiple_matches_only_one_failure_per_alias_code(self):
        """Two matching aliases on the same AliasCode → still only one failure
        thanks to the early `break`."""
        rule = RuleDDF00063()
        data = self._data(
            [
                {
                    "id": "A1",
                    "standardCode": {
                        "codeSystem": "CT",
                        "codeSystemVersion": "1",
                        "code": "X",
                    },
                    "standardCodeAliases": [
                        {
                            "codeSystem": "CT",
                            "codeSystemVersion": "1",
                            "code": "X",
                        },
                        {
                            "codeSystem": "CT",
                            "codeSystemVersion": "1",
                            "code": "X",
                        },
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        # One failure per AliasCode, not per alias.
        assert rule.errors().count() == 1
