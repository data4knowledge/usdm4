"""Tests for RuleDDF00172 — exactly one sponsor StudyIdentifier per StudyVersion."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00172 import RuleDDF00172
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00172:
    def test_metadata(self):
        rule = RuleDDF00172()
        assert rule._rule == "DDF00172"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def test_exactly_one_sponsor_passes(self):
        rule = RuleDDF00172()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "roles": [{"code": {"code": "C70793"}, "organizationIds": ["O1"]}],
                    "studyIdentifiers": [{"scopeId": "O1"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_zero_sponsor_identifiers_fails(self):
        rule = RuleDDF00172()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "roles": [{"code": {"code": "C70793"}, "organizationIds": ["O1"]}],
                    "studyIdentifiers": [{"scopeId": "OTHER"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "found 0" in rule.errors().dump()

    def test_multiple_sponsor_identifiers_fails(self):
        rule = RuleDDF00172()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "roles": [
                        {"code": {"code": "C70793"}, "organizationIds": ["O1", "O2"]}
                    ],
                    "studyIdentifiers": [{"scopeId": "O1"}, {"scopeId": "O2"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "found 2" in rule.errors().dump()

    def test_non_sponsor_role_ignored(self):
        rule = RuleDDF00172()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "roles": [{"code": {"code": "OTHER"}, "organizationIds": ["O1"]}],
                    "studyIdentifiers": [{"scopeId": "O1"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "found 0" in rule.errors().dump()
