"""Tests for RuleDDF00151 — global scope => exactly one scope."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00151 import RuleDDF00151
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00151:
    def test_metadata(self):
        rule = RuleDDF00151()
        assert rule._rule == "DDF00151"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, dates):
        data = MagicMock()
        data.instances_by_klass.return_value = dates
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_global_passes(self):
        rule = RuleDDF00151()
        data = self._data(
            [
                {
                    "id": "D1",
                    "geographicScopes": [
                        {"type": {"code": "US"}},
                        {"type": {"code": "EU"}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_global_alone_passes(self):
        rule = RuleDDF00151()
        data = self._data(
            [{"id": "D1", "geographicScopes": [{"type": {"code": "C68846"}}]}]
        )
        assert rule.validate({"data": data}) is True

    def test_global_plus_other_fails(self):
        rule = RuleDDF00151()
        data = self._data(
            [
                {
                    "id": "D1",
                    "geographicScopes": [
                        {"type": {"code": "C68846"}},
                        {"type": {"code": "US"}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
