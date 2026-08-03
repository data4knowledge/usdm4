"""Tests for RuleDDF00202 — sponsor StudyRole → exactly one known organization."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00202 import RuleDDF00202
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00202:
    def test_metadata(self):
        rule = RuleDDF00202()
        assert rule._rule == "DDF00202"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def test_one_matching_org_passes(self):
        rule = RuleDDF00202()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "organizations": [{"id": "O1"}],
                    "roles": [
                        {
                            "id": "R1",
                            "code": {"code": "C70793"},
                            "organizationIds": ["O1"],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_non_sponsor_role_ignored(self):
        rule = RuleDDF00202()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "organizations": [],
                    "roles": [
                        {
                            "id": "R1",
                            "code": {"code": "OTHER"},
                            "organizationIds": [],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_zero_orgs_fails(self):
        rule = RuleDDF00202()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "organizations": [],
                    "roles": [
                        {
                            "id": "R1",
                            "code": {"code": "C70793"},
                            "organizationIds": [],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "found 0 id(s)" in rule.errors().dump()

    def test_multiple_orgs_fails(self):
        rule = RuleDDF00202()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "organizations": [{"id": "O1"}, {"id": "O2"}],
                    "roles": [
                        {
                            "id": "R1",
                            "code": {"code": "C70793"},
                            "organizationIds": ["O1", "O2"],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "found 2 id(s)" in rule.errors().dump()

    def test_unresolved_org_fails(self):
        rule = RuleDDF00202()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "organizations": [],
                    "roles": [
                        {
                            "id": "R1",
                            "code": {"code": "C70793"},
                            "organizationIds": ["UNKNOWN"],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "0 matching" in rule.errors().dump()
