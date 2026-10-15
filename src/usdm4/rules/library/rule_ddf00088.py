# MANUAL: do not regenerate
#
# Compare two epoch orderings per main ScheduleTimeline:
#   A. The StudyDesign's epoch linked list, from the head (previousId=null)
#      along nextId.
#   B. The main timeline walked from entryId along defaultConditionId through
#      activity and decision instances, a loop left by its first condition
#      not yet walked (rules/timeline_walk.py, issue 89); each activity
#      instance's epochId, first occurrence only.
# Flag when A, restricted to the epochs met in B, differs from B: a epoch
# used only by another timeline is never on the main walk. Also flag several
# chain heads and a cycle in either walk.
from usdm4.rules.rule_template import RuleTemplate
from usdm4.rules.timeline_walk import first_occurrences, walk_main_timeline


STUDY_DESIGN_KLASSES = [
    "StudyDesign",
    "InterventionalStudyDesign",
    "ObservationalStudyDesign",
]


def _walk_chain(by_id, head_id, next_attr):
    """Walk a linked-list by attr name. Returns (ordered_ids, cycle_detected)."""
    visited: set = set()
    order = []
    cur = head_id
    while cur:
        if cur in visited:
            return order, True
        visited.add(cur)
        order.append(cur)
        node = by_id.get(cur)
        if not isinstance(node, dict):
            break
        cur = node.get(next_attr)
    return order, False


class RuleDDF00088(RuleTemplate):
    """
    DDF00088: Epoch ordering using previous and next attributes is expected to be consistent with the order of corresponding scheduled activity instances according to their specified default conditions.

    Applies to: StudyEpoch
    Attributes: previousId, nextId
    """

    def __init__(self):
        super().__init__(
            "DDF00088",
            RuleTemplate.WARNING,
            "Epoch ordering using previous and next attributes is expected to be consistent with the order of corresponding scheduled activity instances according to their specified default conditions.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in STUDY_DESIGN_KLASSES:
            for design in data.instances_by_klass(klass):
                epochs = [e for e in design.get("epochs") or [] if isinstance(e, dict)]
                if not epochs:
                    continue
                epochs_by_id = {e.get("id"): e for e in epochs if e.get("id")}
                design_epoch_ids = set(epochs_by_id)

                heads = [e.get("id") for e in epochs if not e.get("previousId")]
                if len(heads) > 1:
                    self._add_failure(
                        f"StudyDesign has {len(heads)} epoch chain heads (previousId=null) — expected 1",
                        "StudyEpoch",
                        "previousId",
                        data.path_by_id(design["id"]),
                    )
                if not heads:
                    continue
                order_a, cycle_a = _walk_chain(epochs_by_id, heads[0], "nextId")
                if cycle_a:
                    self._add_failure(
                        "Cycle detected while walking StudyEpoch prev/next chain",
                        "StudyEpoch",
                        "nextId",
                        data.path_by_id(design["id"]),
                    )

                timelines = [
                    t
                    for t in design.get("scheduleTimelines") or []
                    if isinstance(t, dict) and t.get("mainTimeline")
                ]
                for timeline in timelines:
                    if not timeline.get("entryId"):
                        continue
                    # Issue 89: walk through decisions as well as activity
                    # instances, and compare only the epochs the walk meets —
                    # one used only by another timeline cannot be on it.
                    walked, cycle_b = walk_main_timeline(timeline)
                    if cycle_b:
                        self._add_failure(
                            "Cycle detected while walking ScheduledActivityInstance defaultConditionId chain",
                            "ScheduledActivityInstance",
                            "defaultConditionId",
                            data.path_by_id(timeline["id"]),
                        )
                    order_b = first_occurrences(
                        [
                            s.get("epochId")
                            for s in walked
                            if s.get("epochId") in design_epoch_ids
                        ]
                    )
                    met = set(order_b)
                    chain = [x for x in order_a if x in met]
                    if chain != order_b:
                        self._add_failure(
                            f"StudyEpoch prev/next order {chain} does not match order derived from SAI flow {order_b}",
                            "StudyEpoch",
                            "previousId, nextId",
                            data.path_by_id(timeline["id"]),
                        )
        return self._result()
