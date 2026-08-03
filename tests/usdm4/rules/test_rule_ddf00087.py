"""Tests for RuleDDF00087 — Encounter prev/next order vs SAI flow."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00087 import (
    RuleDDF00087,
    _dedupe_consecutive,
    _walk_encounter_chain,
    _walk_sai_chain,
)
from usdm4.rules.rule_template import RuleTemplate


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def test_walk_encounter_chain_linear():
    by_id = {
        "E1": {"id": "E1", "nextId": "E2"},
        "E2": {"id": "E2", "nextId": "E3"},
        "E3": {"id": "E3"},
    }
    order, cycle = _walk_encounter_chain(by_id, "E1")
    assert order == ["E1", "E2", "E3"]
    assert cycle is False


def test_walk_encounter_chain_detects_cycle():
    by_id = {
        "E1": {"id": "E1", "nextId": "E2"},
        "E2": {"id": "E2", "nextId": "E1"},  # cycle back
    }
    _, cycle = _walk_encounter_chain(by_id, "E1")
    assert cycle is True


def test_walk_encounter_chain_stops_at_non_dict():
    """If next points at something not in the map, loop breaks cleanly."""
    by_id = {"E1": {"id": "E1", "nextId": "MISSING"}}
    order, cycle = _walk_encounter_chain(by_id, "E1")
    assert order == ["E1", "MISSING"]  # appended before lookup finds nothing
    assert cycle is False


def test_walk_sai_chain_linear():
    by_id = {
        "S1": {"id": "S1", "defaultConditionId": "S2"},
        "S2": {"id": "S2"},
    }
    order, cycle = _walk_sai_chain(by_id, "S1")
    assert order == ["S1", "S2"]
    assert cycle is False


def test_walk_sai_chain_cycle():
    by_id = {
        "S1": {"id": "S1", "defaultConditionId": "S2"},
        "S2": {"id": "S2", "defaultConditionId": "S1"},
    }
    _, cycle = _walk_sai_chain(by_id, "S1")
    assert cycle is True


def test_dedupe_consecutive_preserves_order_removes_repeats():
    assert _dedupe_consecutive(["A", "A", "B", "B", "A"]) == ["A", "B", "A"]
    assert _dedupe_consecutive([]) == []


# ---------------------------------------------------------------------------
# Rule validate()
# ---------------------------------------------------------------------------


class TestRuleDDF00087:
    def test_metadata(self):
        rule = RuleDDF00087()
        assert rule._rule == "DDF00087"
        assert rule._level == RuleTemplate.WARNING

    def _data(self, designs_by_klass):
        data = MagicMock()

        def _inst(k):
            return designs_by_klass.get(k, [])

        data.instances_by_klass.side_effect = _inst
        data.path_by_id.return_value = "$.path"
        return data

    def test_design_without_encounters_is_skipped(self):
        rule = RuleDDF00087()
        data = self._data(
            {"InterventionalStudyDesign": [{"id": "D1", "encounters": []}]}
        )
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_multiple_chain_heads_fail(self):
        rule = RuleDDF00087()
        design = {
            "id": "D1",
            "encounters": [
                {"id": "E1"},  # no previousId → head
                {"id": "E2"},  # no previousId → head
            ],
            "scheduleTimelines": [],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
        # Multi-head failure logged
        assert rule.errors().count() == 1

    def test_no_heads_is_skipped(self):
        """All encounters have a previousId → no head found → skip silently."""
        rule = RuleDDF00087()
        design = {
            "id": "D1",
            "encounters": [
                {"id": "E1", "previousId": "E2"},
                {"id": "E2", "previousId": "E1"},
            ],
            "scheduleTimelines": [],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        # Only one head check output is multi-head failure — but we have 0 heads,
        # so no failure is logged and loop continues.
        assert rule.validate({"data": data}) is True

    def test_encounter_cycle_detected(self):
        rule = RuleDDF00087()
        design = {
            "id": "D1",
            "encounters": [
                {"id": "E1", "nextId": "E2"},  # head
                {"id": "E2", "previousId": "E1", "nextId": "E1"},  # cycle
            ],
            "scheduleTimelines": [],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
        # The cycle failure is logged
        assert rule.errors().count() >= 1

    def test_matching_encounter_and_sai_orders_pass(self):
        """Encounter chain [E1,E2] matches SAI flow that visits E1 then E2."""
        rule = RuleDDF00087()
        design = {
            "id": "D1",
            "encounters": [
                {"id": "E1", "nextId": "E2"},  # head
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
                            "encounterId": "E1",
                            "defaultConditionId": "S2",
                        },
                        {
                            "id": "S2",
                            "instanceType": "ScheduledActivityInstance",
                            "encounterId": "E2",
                        },
                    ],
                }
            ],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is True
        assert rule.errors().count() == 0

    def test_mismatched_orders_fail(self):
        rule = RuleDDF00087()
        design = {
            "id": "D1",
            "encounters": [
                {"id": "E1", "nextId": "E2"},  # head, chain = [E1, E2]
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
                            "encounterId": "E2",  # SAI order puts E2 first
                            "defaultConditionId": "S2",
                        },
                        {
                            "id": "S2",
                            "instanceType": "ScheduledActivityInstance",
                            "encounterId": "E1",
                        },
                    ],
                }
            ],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is False
        assert rule.errors().count() == 1

    def test_timeline_without_entry_id_is_skipped(self):
        rule = RuleDDF00087()
        design = {
            "id": "D1",
            "encounters": [{"id": "E1"}],
            "scheduleTimelines": [{"id": "T1", "mainTimeline": True, "entryId": None}],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is True

    def test_non_main_timeline_is_ignored(self):
        rule = RuleDDF00087()
        design = {
            "id": "D1",
            "encounters": [{"id": "E1"}],
            "scheduleTimelines": [
                {"id": "T1", "mainTimeline": False, "entryId": "S1", "instances": []}
            ],
        }
        data = self._data({"InterventionalStudyDesign": [design]})
        assert rule.validate({"data": data}) is True
