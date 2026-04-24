"""Tests for RuleDDF00201 — exactly one sponsor StudyRole per StudyVersion."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00201 import RuleDDF00201, SPONSOR_ROLE_CODE
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00201:
    def test_metadata(self):
        rule = RuleDDF00201()
        assert rule._rule == "DDF00201"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def test_exactly_one_passes(self):
        rule = RuleDDF00201()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "roles": [
                        {"code": {"code": SPONSOR_ROLE_CODE}},
                        {"code": {"code": "C99"}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_zero_fails(self):
        rule = RuleDDF00201()
        data = self._data([{"id": "SV1", "roles": []}])
        assert rule.validate({"data": data}) is False
        assert "found 0" in rule.errors().dump()

    def test_two_fails(self):
        rule = RuleDDF00201()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "roles": [
                        {"code": {"code": SPONSOR_ROLE_CODE}},
                        {"code": {"code": SPONSOR_ROLE_CODE}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "found 2" in rule.errors().dump()

    def test_non_dict_code_ignored(self):
        rule = RuleDDF00201()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "roles": [
                        {"code": "not-a-dict"},
                        {"code": {"code": SPONSOR_ROLE_CODE}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
