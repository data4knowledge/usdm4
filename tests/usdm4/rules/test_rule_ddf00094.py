"""Tests for RuleDDF00094 — StudyVersion dates with global scope must be unique per type."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00094 import GLOBAL_CODE, RuleDDF00094
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00094:
    def test_metadata(self):
        rule = RuleDDF00094()
        assert rule._rule == "DDF00094"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def test_non_dict_date_skipped(self):
        rule = RuleDDF00094()
        data = self._data([{"id": "SV1", "dateValues": ["bogus", None]}])
        assert rule.validate({"data": data}) is True

    def test_missing_type_skipped(self):
        rule = RuleDDF00094()
        data = self._data([{"id": "SV1", "dateValues": [{"id": "D1"}]}])
        assert rule.validate({"data": data}) is True

    def test_no_global_scope_passes(self):
        rule = RuleDDF00094()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "dateValues": [
                        {
                            "id": "D1",
                            "type": {"code": "C1"},
                            "geographicScopes": [{"type": {"code": "US"}}],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_global_plus_other_date_fails(self):
        rule = RuleDDF00094()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "dateValues": [
                        {
                            "id": "D1",
                            "type": {"code": "C1"},
                            "geographicScopes": [{"type": {"code": GLOBAL_CODE}}],
                        },
                        {
                            "id": "D2",
                            "type": {"code": "C1"},
                            "geographicScopes": [{"type": {"code": "US"}}],
                        },
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 2

    def test_global_alone_passes(self):
        rule = RuleDDF00094()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "dateValues": [
                        {
                            "id": "D1",
                            "type": {"code": "C1"},
                            "geographicScopes": [{"type": {"code": GLOBAL_CODE}}],
                        }
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True
