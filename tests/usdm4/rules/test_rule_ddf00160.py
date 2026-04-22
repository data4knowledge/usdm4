"""Tests for RuleDDF00160 — Activity with children mustn't reference leaves."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00160 import RuleDDF00160, _is_populated
from usdm4.rules.rule_template import RuleTemplate


def test_is_populated_variants():
    assert _is_populated(None) is False
    assert _is_populated("  ") is False
    assert _is_populated("x") is True
    assert _is_populated([]) is False
    assert _is_populated([1]) is True
    assert _is_populated({}) is False
    assert _is_populated({"a": 1}) is True
    assert _is_populated(42) is True


class TestRuleDDF00160:
    def test_metadata(self):
        rule = RuleDDF00160()
        assert rule._rule == "DDF00160"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, activities):
        data = MagicMock()
        data.instances_by_klass.return_value = activities
        data.path_by_id.return_value = "$.path"
        return data

    def test_no_children_skipped(self):
        rule = RuleDDF00160()
        data = self._data([{"id": "A1", "timelineId": "TL1"}])
        assert rule.validate({"data": data}) is True

    def test_children_no_refs_passes(self):
        rule = RuleDDF00160()
        data = self._data([{"id": "A1", "childIds": ["A2"]}])
        assert rule.validate({"data": data}) is True

    def test_children_with_refs_fails(self):
        rule = RuleDDF00160()
        data = self._data(
            [
                {
                    "id": "A1",
                    "childIds": ["A2"],
                    "biomedicalConceptIds": ["BC1"],
                    "timelineId": "TL1",
                }
            ]
        )
        assert rule.validate({"data": data}) is False
        dump = rule.errors().dump()
        assert "biomedicalConceptIds" in dump
        assert "timelineId" in dump
