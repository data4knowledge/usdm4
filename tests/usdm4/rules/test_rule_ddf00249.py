"""Tests for RuleDDF00249 — EligibilityCriterionItem must be used by at least one criterion."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00249 import RuleDDF00249
from usdm4.rules.rule_template import RuleTemplate


class TestRuleDDF00249:
    def test_metadata(self):
        rule = RuleDDF00249()
        assert rule._rule == "DDF00249"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, criteria, items):
        """Build a DataStore-like mock returning ``criteria`` for
        ``EligibilityCriterion`` and ``items`` for ``EligibilityCriterionItem``.
        """

        def by_klass(klass):
            if klass == "EligibilityCriterion":
                return criteria
            if klass == "EligibilityCriterionItem":
                return items
            return []

        data = MagicMock()
        data.instances_by_klass.side_effect = by_klass
        data.path_by_id.return_value = "$.path"
        return data

    def test_used_item_passes(self):
        rule = RuleDDF00249()
        data = self._data(
            criteria=[{"id": "EC1", "criterionItemId": "ITEM1"}],
            items=[{"id": "ITEM1"}],
        )
        assert rule.validate({"data": data}) is True

    def test_unused_item_fails(self):
        rule = RuleDDF00249()
        data = self._data(
            criteria=[{"id": "EC1", "criterionItemId": "ITEM1"}],
            items=[{"id": "ITEM1"}, {"id": "ITEM2"}],
        )
        assert rule.validate({"data": data}) is False
        # WARNING-level rules don't surface in the default error dump;
        # check the count instead.
        assert rule.errors().count() == 1

    def test_no_items_passes(self):
        rule = RuleDDF00249()
        data = self._data(criteria=[], items=[])
        assert rule.validate({"data": data}) is True
