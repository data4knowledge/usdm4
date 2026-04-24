"""Tests for RuleDDF00115 — StudyVersion must have an Official Study Title."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00115 import RuleDDF00115
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00115:
    def test_metadata(self):
        rule = RuleDDF00115()
        assert rule._rule == "DDF00115"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def test_has_official_passes(self):
        rule = RuleDDF00115()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "titles": [
                        {"id": "T1", "type": {"code": "C207616"}},
                        {"id": "T2", "type": {"code": "OTHER"}},
                    ],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_no_titles_fails(self):
        rule = RuleDDF00115()
        data = self._data([{"id": "SV1"}])
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_no_official_fails(self):
        rule = RuleDDF00115()
        data = self._data(
            [{"id": "SV1", "titles": [{"id": "T1", "type": {"code": "OTHER"}}]}]
        )
        assert rule.validate({"data": data}) is False

    def test_non_dict_title_ignored(self):
        rule = RuleDDF00115()
        data = self._data([{"id": "SV1", "titles": ["bad", None]}])
        assert rule.validate({"data": data}) is False
