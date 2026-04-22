"""Tests for RuleDDF00181 — SDDV.dateValues unique per (type, geographic scopes)."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00181 import RuleDDF00181, _date_key
from usdm4.rules.rule_template import RuleTemplate


def test_date_key_shape():
    type_code, scope_codes = _date_key(
        {
            "type": {"code": "T1"},
            "geographicScopes": [{"type": {"code": "S1"}}, {"type": {"code": "S2"}}],
        }
    )
    assert type_code == "T1"
    assert scope_codes == frozenset({"S1", "S2"})


def test_date_key_non_dict_type():
    type_code, _ = _date_key({"type": "bad"})
    assert type_code is None


class TestRuleDDF00181:
    def test_metadata(self):
        rule = RuleDDF00181()
        assert rule._rule == "DDF00181"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, sddvs):
        data = MagicMock()
        data.instances_by_klass.return_value = sddvs
        data.path_by_id.return_value = "$.path"
        return data

    def test_missing_type_code_skipped(self):
        rule = RuleDDF00181()
        data = self._data(
            [
                {
                    "id": "SDDV1",
                    "dateValues": [
                        {"id": "D1", "type": None},
                        {"id": "D2", "type": None},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_unique_combinations_pass(self):
        rule = RuleDDF00181()
        data = self._data(
            [
                {
                    "id": "SDDV1",
                    "dateValues": [
                        {"id": "D1", "type": {"code": "T1"}, "geographicScopes": []},
                        {"id": "D2", "type": {"code": "T2"}, "geographicScopes": []},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00181()
        data = self._data(
            [
                {
                    "id": "SDDV1",
                    "dateValues": [
                        {"id": "D1", "type": {"code": "T1"}, "geographicScopes": []},
                        {"id": "D2", "type": {"code": "T1"}, "geographicScopes": []},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
