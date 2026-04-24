"""Tests for RuleDDF00088 — Epoch prev/next order vs SAI flow."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00088 import (
    RuleDDF00088,
    _dedupe_consecutive,
    _walk_chain,
)
from usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# _walk_chain
# ---------------------------------------------------------------------------


def test_walk_chain_linear():
    by_id = {
        "A": {"id": "A", "nextId": "B"},
        "B": {"id": "B", "nextId": "C"},
        "C": {"id": "C"},
    }
    order, cycle = _walk_chain(by_id, "A", "nextId")
    assert order == ["A", "B", "C"]
    assert cycle is False


def test_walk_chain_with_custom_attr():
    """The function accepts an arbitrary `next_attr` name."""
    by_id = {
        "S1": {"id": "S1", "defaultConditionId": "S2"},
        "S2": {"id": "S2"},
    }
    order, _ = _walk_chain(by_id, "S1", "defaultConditionId")
    assert order == ["S1", "S2"]


def test_walk_chain_cycle_returns_true():
    by_id = {
        "A": {"id": "A", "nextId": "B"},
        "B": {"id": "B", "nextId": "A"},
    }
    _, cycle = _walk_chain(by_id, "A", "nextId")
    assert cycle is True


def test_dedupe_consecutive_preserves_non_repeats():
    assert _dedupe_consecutive(["A", "B", "A"]) == ["A", "B", "A"]
    assert _dedupe_consecutive([]) == []


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00088:
    def test_metadata(self):
        rule = RuleDDF00088()
        assert rule._rule == "DDF00088"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, designs_by_klass):
        data = MagicMock()
        data.instances_by_klass.side_effect = lambda k: designs_by_klass.get(k, [])
        data.path_by_id.return_value = "$.path"
        return data

    def test_design_without_epochs_is_skipped(self):
        rule = RuleDDF00088()
        data = self._data({"InterventionalStudyDesign": [{"id": "D1", "epochs": []}]})
        assert rule.validate({"data": data}) is True

    def test_multiple_chain_heads_fail(self):
        rule = RuleDDF00088()
        design = {
            "id": "D1",
            "epochs": [{"id": "E1"}, {"id": "E2"}],  # both head
            "scheduleTimelines": [],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_epoch_chain_cycle_detected(self):
        rule = RuleDDF00088()
        design = {
            "id": "D1",
            "epochs": [
                {"id": "E1", "nextId": "E2"},
                {"id": "E2", "previousId": "E1", "nextId": "E1"},
            ],
            "scheduleTimelines": [],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() >= 1

    def test_matching_orders_pass(self):
        rule = RuleDDF00088()
        design = {
            "id": "D1",
            "epochs": [
                {"id": "E1", "nextId": "E2"},
                {"id": "E2", "previousId": "E1"},
            ],
            "scheduleTimelines": [
                {
                    "id": "T1",
                    "mainTimeline": True,
                    "entryId": "S1",
                    "instances": [
                        {
                            "id": "S1",
                            "instanceType": "ScheduledActivityInstance",
                            "epochId": "E1",
                            "defaultConditionId": "S2",
                        },
                        {
                            "id": "S2",
                            "instanceType": "ScheduledActivityInstance",
                            "epochId": "E2",
                        },
                    ],
                }
            ],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is True

    def test_mismatched_orders_fail(self):
        rule = RuleDDF00088()
        design = {
            "id": "D1",
            "epochs": [
                {"id": "E1", "nextId": "E2"},
                {"id": "E2", "previousId": "E1"},
            ],
            "scheduleTimelines": [
                {
                    "id": "T1",
                    "mainTimeline": True,
                    "entryId": "S1",
                    "instances": [
                        {
                            "id": "S1",
                            "instanceType": "ScheduledActivityInstance",
                            "epochId": "E2",  # flipped
                            "defaultConditionId": "S2",
                        },
                        {
                            "id": "S2",
                            "instanceType": "ScheduledActivityInstance",
                            "epochId": "E1",
                        },
                    ],
                }
            ],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_timeline_without_entry_id_is_skipped(self):
        rule = RuleDDF00088()
        design = {
            "id": "D1",
            "epochs": [{"id": "E1"}],
            "scheduleTimelines": [{"id": "T1", "mainTimeline": True, "entryId": None}],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is True
