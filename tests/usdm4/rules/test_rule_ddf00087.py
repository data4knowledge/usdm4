"""Tests for RuleDDF00087 — Encounter prev/next order vs SAI flow."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00087 import (
    RuleDDF00087,
    _walk_encounter_chain,
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


# ---------------------------------------------------------------------------
# Issue 89: a walk through decisions, and items used only by other timelines
# ---------------------------------------------------------------------------


def _sai(id_, item, following=None):
    return {
        "id": id_,
        "instanceType": "ScheduledActivityInstance",
        "encounterId": item,
        "defaultConditionId": following,
    }


def _chain(*ids):
    return [
        {
            "id": i,
            "previousId": ids[n - 1] if n else None,
            "nextId": ids[n + 1] if n + 1 < len(ids) else None,
        }
        for n, i in enumerate(ids)
    ]


def _validate(design):
    data = MagicMock()
    data.instances_by_klass.side_effect = lambda k: (
        [design] if k == "InterventionalStudyDesign" else []
    )
    data.path_by_id.return_value = "$.path"
    rule = RuleDDF00087()
    return rule.validate({"data": data}), rule


def _looping(chain):
    """S1 (E1) -> S2 (E2) -> decision: default loops back to S2, the
    condition leaves to S3 (E3)."""
    return {
        "id": "D1",
        "encounters": chain,
        "scheduleTimelines": [
            {
                "id": "T1",
                "mainTimeline": True,
                "entryId": "S1",
                "instances": [
                    _sai("S1", "E1", "S2"),
                    _sai("S2", "E2", "X1"),
                    {
                        "id": "X1",
                        "instanceType": "ScheduledDecisionInstance",
                        "defaultConditionId": "S2",
                        "conditionAssignments": [{"conditionTargetId": "S3"}],
                    },
                    _sai("S3", "E3"),
                ],
            }
        ],
    }


def test_issue_89_a_walk_continues_past_a_repeat():
    passed, rule = _validate(_looping(_chain("E1", "E2", "E3")))
    assert passed is True
    assert rule.errors().count() == 0


def test_issue_89_a_swapped_chain_still_fails():
    passed, _ = _validate(_looping(_chain("E1", "E3", "E2")))
    assert passed is False


def test_issue_89_an_item_only_on_another_timeline_is_not_counted():
    design = _looping(_chain("E1", "E2", "E3", "E9"))
    design["scheduleTimelines"].append(
        {
            "id": "T2",
            "mainTimeline": False,
            "entryId": "S9",
            "instances": [_sai("S9", "E9")],
        }
    )
    passed, rule = _validate(design)
    assert passed is True
    assert rule.errors().count() == 0


def test_issue_89_a_decision_with_no_way_forward_ends_the_walk():
    design = _looping(_chain("E1", "E2"))
    design["scheduleTimelines"][0]["instances"][2]["conditionAssignments"] = []
    passed, _ = _validate(design)
    assert passed is True


def test_issue_89_a_cycle_between_activity_instances_is_still_reported():
    design = _looping(_chain("E1", "E2"))
    design["scheduleTimelines"][0]["instances"][1]["defaultConditionId"] = "S1"
    passed, rule = _validate(design)
    assert passed is False
    assert rule.errors().count() >= 1
