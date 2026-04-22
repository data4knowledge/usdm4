"""Tests for RuleDDF00182 — global-scope dates uniqueness per SDD version."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00182 import GLOBAL_CODE, RuleDDF00182
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00182:
    def test_metadata(self):
        rule = RuleDDF00182()
        assert rule._rule == "DDF00182"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, sddvs):
        data = MagicMock()
        data.instances_by_klass.return_value = sddvs
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_global_scope_passes(self):
        rule = RuleDDF00182()
        data = self._data(
            [
                {
                    "id": "SDDV1",
                    "dateValues": [
                        {
                            "id": "D1",
                            "type": {"code": "T1"},
                            "geographicScopes": [{"type": {"code": "US"}}],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_non_dict_date_skipped(self):
        rule = RuleDDF00182()
        data = self._data([{"id": "SDDV1", "dateValues": ["bogus"]}])
        assert rule.validate({"data": data}) is True

    def test_missing_type_skipped(self):
        rule = RuleDDF00182()
        data = self._data(
            [{"id": "SDDV1", "dateValues": [{"id": "D1", "geographicScopes": []}]}]
        )
        assert rule.validate({"data": data}) is True

    def test_global_alone_passes(self):
        rule = RuleDDF00182()
        data = self._data(
            [
                {
                    "id": "SDDV1",
                    "dateValues": [
                        {
                            "id": "D1",
                            "type": {"code": "T1"},
                            "geographicScopes": [{"type": {"code": GLOBAL_CODE}}],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_global_plus_other_fails(self):
        rule = RuleDDF00182()
        data = self._data(
            [
                {
                    "id": "SDDV1",
                    "dateValues": [
                        {
                            "id": "D1",
                            "type": {"code": "T1"},
                            "geographicScopes": [{"type": {"code": GLOBAL_CODE}}],
                        },
                        {
                            "id": "D2",
                            "type": {"code": "T1"},
                            "geographicScopes": [{"type": {"code": "US"}}],
                        },
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2
