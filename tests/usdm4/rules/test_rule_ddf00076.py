"""Tests for RuleDDF00076 — Activity must not reference same BC directly and via category."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00076 import RuleDDF00076
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00076:
    def test_metadata(self):
        rule = RuleDDF00076()
        assert rule._rule == "DDF00076"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, activities, id_map=None):
        data = MagicMock()
        data.instances_by_klass.return_value = activities
        data.path_by_id.return_value = "$.path"
        data.instance_by_id.side_effect = lambda tid: (id_map or {}).get(tid)
        return data

    def test_no_direct_bcs_skipped(self):
        rule = RuleDDF00076()
        data = self._data([{"id": "A1"}])
        assert rule.validate({"data": data}) is True

    def test_non_dict_category_skipped(self):
        rule = RuleDDF00076()
        data = self._data(
            [{"id": "A1", "biomedicalConceptIds": ["BC1"], "bcCategoryIds": ["CAT1"]}],
            id_map={"CAT1": None},
        )
        assert rule.validate({"data": data}) is True

    def test_no_overlap_passes(self):
        rule = RuleDDF00076()
        data = self._data(
            [{"id": "A1", "biomedicalConceptIds": ["BC1"], "bcCategoryIds": ["CAT1"]}],
            id_map={"CAT1": {"id": "CAT1", "memberIds": ["BC2"]}},
        )
        assert rule.validate({"data": data}) is True

    def test_overlap_fails(self):
        rule = RuleDDF00076()
        data = self._data(
            [{"id": "A1", "biomedicalConceptIds": ["BC1"], "bcCategoryIds": ["CAT1"]}],
            id_map={"CAT1": {"id": "CAT1", "memberIds": ["BC1", "BC2"]}},
        )
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1
