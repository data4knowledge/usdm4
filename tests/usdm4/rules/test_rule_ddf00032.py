"""Tests for RuleDDF00032 — StudyVersion.businessTherapeuticAreas distinct."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00032 import RuleDDF00032
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00032:
    def test_metadata(self):
        rule = RuleDDF00032()
        assert rule._rule == "DDF00032"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, versions):
        data = MagicMock()
        data.instances_by_klass.return_value = versions
        data.path_by_id.return_value = "$.path"
        return data

    def test_distinct_passes(self):
        rule = RuleDDF00032()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "businessTherapeuticAreas": [{"code": "A"}, {"code": "B"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is True

    def test_duplicate_fails(self):
        rule = RuleDDF00032()
        data = self._data(
            [
                {
                    "id": "SV1",
                    "businessTherapeuticAreas": [{"code": "A"}, {"code": "A"}],
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        assert "Duplicate" in rule.errors().dump()

    def test_non_dict_handled(self):
        rule = RuleDDF00032()
        data = self._data([{"id": "SV1", "businessTherapeuticAreas": ["X", "X"]}])
        assert rule.validate({"data": data}) is False
