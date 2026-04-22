"""Tests for RuleDDF00047 — StudyCell.elementIds must live in same StudyDesign."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00047 import RuleDDF00047
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00047:
    def test_metadata(self):
        rule = RuleDDF00047()
        assert rule._rule == "DDF00047"
        assert rule._level == RuleTemplate.ERROR

    def _data(self, cells, parent_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = cells
        data.path_by_id.return_value = "$.path"
        data.parent_by_klass.side_effect = lambda tid, _k: (parent_map or {}).get(tid)
        return data

    def test_cell_without_parent_skipped(self):
        rule = RuleDDF00047()
        data = self._data([{"id": "C1", "elementIds": ["E1"]}])
        assert rule.validate({"data": data}) is True

    def test_blank_element_id_skipped(self):
        rule = RuleDDF00047()
        data = self._data(
            [{"id": "C1", "elementIds": ["", None]}],
            parent_map={"C1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_element_without_parent_skipped(self):
        rule = RuleDDF00047()
        data = self._data(
            [{"id": "C1", "elementIds": ["E1"]}],
            parent_map={"C1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_same_design_passes(self):
        rule = RuleDDF00047()
        data = self._data(
            [{"id": "C1", "elementIds": ["E1"]}],
            parent_map={"C1": {"id": "SD1"}, "E1": {"id": "SD1"}},
        )
        assert rule.validate({"data": data}) is True

    def test_different_design_fails(self):
        rule = RuleDDF00047()
        data = self._data(
            [{"id": "C1", "elementIds": ["E1"]}],
            parent_map={"C1": {"id": "SD1"}, "E1": {"id": "SD2"}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
