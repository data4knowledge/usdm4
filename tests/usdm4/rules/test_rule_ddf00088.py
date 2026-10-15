"""Tests for RuleDDF00088 — Epoch prev/next order vs SAI flow."""

from unittest.mock import MagicMock

from usdm4.rules.library.rule_ddf00088 import (
    RuleDDF00088,
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


# ---------------------------------------------------------------------------
# Issue 89: a walk through decisions, and items used only by other timelines
# ---------------------------------------------------------------------------


def _sai(id_, item, following=None):
    return {
        "id": id_,
        "instanceType": "ScheduledActivityInstance",
        "epochId": item,
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
    rule = RuleDDF00088()
    return rule.validate({"data": data}), rule


def _looping(chain):
    """S1 (P1) -> S2 (P2) -> decision: default loops back to S2, the
    condition leaves to S3 (P3)."""
    return {
        "id": "D1",
        "epochs": chain,
        "scheduleTimelines": [
            {
                "id": "T1",
                "mainTimeline": True,
                "entryId": "S1",
                "instances": [
                    _sai("S1", "P1", "S2"),
                    _sai("S2", "P2", "X1"),
                    {
                        "id": "X1",
                        "instanceType": "ScheduledDecisionInstance",
                        "defaultConditionId": "S2",
                        "conditionAssignments": [{"conditionTargetId": "S3"}],
                    },
                    _sai("S3", "P3"),
                ],
            }
        ],
    }


def test_issue_89_a_walk_continues_past_a_repeat():
    passed, rule = _validate(_looping(_chain("P1", "P2", "P3")))
    assert passed is True
    assert rule.errors().count() == 0


def test_issue_89_a_swapped_chain_still_fails():
    passed, _ = _validate(_looping(_chain("P1", "P3", "P2")))
    assert passed is False


def test_issue_89_an_item_only_on_another_timeline_is_not_counted():
    design = _looping(_chain("P1", "P2", "P3", "P9"))
    design["scheduleTimelines"].append(
        {
            "id": "T2",
            "mainTimeline": False,
            "entryId": "S9",
            "instances": [_sai("S9", "P9")],
        }
    )
    passed, rule = _validate(design)
    assert passed is True
    assert rule.errors().count() == 0


def test_issue_89_a_decision_with_no_way_forward_ends_the_walk():
    design = _looping(_chain("P1", "P2"))
    design["scheduleTimelines"][0]["instances"][2]["conditionAssignments"] = []
    passed, _ = _validate(design)
    assert passed is True


def test_issue_89_a_cycle_between_activity_instances_is_still_reported():
    design = _looping(_chain("P1", "P2"))
    design["scheduleTimelines"][0]["instances"][1]["defaultConditionId"] = "S1"
    passed, rule = _validate(design)
    assert passed is False
    assert rule.errors().count() >= 1


def test_issue_89_a_chain_pointing_nowhere_stops():
    order, cycle = _walk_chain({"A": {"id": "A", "nextId": "Z"}}, "A", "nextId")
    assert (order, cycle) == (["A", "Z"], False)


def test_issue_89_no_chain_head_is_skipped():
    design = _looping(
        [
            {"id": "P1", "previousId": "P2", "nextId": "P2"},
            {"id": "P2", "previousId": "P1", "nextId": "P1"},
        ]
    )
    passed, _ = _validate(design)
    assert passed is True
