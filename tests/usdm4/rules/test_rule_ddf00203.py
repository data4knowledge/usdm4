"""Tests for RuleDDF00203 — sponsor StudyRole must be applicable to the StudyVersion."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00203 import RuleDDF00203, SPONSOR_ROLE_CODE
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00203:
    def test_metadata(self):
        rule = RuleDDF00203()
        assert rule._rule == "DDF00203"
        assert rule._level == RuleTemplate.ERROR
        assert SPONSOR_ROLE_CODE == "C70793"

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_roles_passes(self):
        rule = RuleDDF00203()
        data = self._data([{"id": "SV1", "roles": None}])
        assert rule.validate({"data": data}) is True

    def test_non_sponsor_role_skipped(self):
        rule = RuleDDF00203()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "roles": [
                        {"id": "R1", "code": {"code": "C99999"}, "appliesToIds": []},
                        "not-a-dict",
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_sponsor_applies_passes(self):
        rule = RuleDDF00203()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "roles": [
                        {
                            "id": "R1",
                            "code": {"code": SPONSOR_ROLE_CODE},
                            "appliesToIds": ["SV1"],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_sponsor_missing_applies_fails(self):
        rule = RuleDDF00203()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "roles": [
                        {
                            "id": "R1",
                            "code": {"code": SPONSOR_ROLE_CODE},
                            "appliesToIds": ["SV2"],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "not applicable" in rule.errors().dump()

    def test_sponsor_code_non_dict_skipped(self):
        rule = RuleDDF00203()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "roles": [{"id": "R1", "code": "plain-string"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
