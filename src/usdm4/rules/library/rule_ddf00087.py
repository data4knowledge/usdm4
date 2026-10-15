# MANUAL: do not regenerate
#
# Compare two encounter orderings per main ScheduleTimeline:
#   A. The StudyDesign's encounter linked list, from the head (previousId=null)
#      along nextId.
#   B. The main timeline walked from entryId along defaultConditionId through
#      activity and decision instances, a loop left by its first condition
#      not yet walked (rules/timeline_walk.py, issue 89); each activity
#      instance's encounterId, first occurrence only.
# Flag when A, restricted to the encounters met in B, differs from B: a encounter
# used only by another timeline is never on the main walk. Also flag several
# chain heads and a cycle in either walk.
from usdm4.rules.rule_template import RuleTemplate
from usdm4.rules.timeline_walk import first_occurrences, walk_main_timeline


STUDY_DESIGN_KLASSES = [
    "StudyDesign",
    "InterventionalStudyDesign",
    "ObservationalStudyDesign",
]


def _walk_encounter_chain(encounters_by_id, head_id, visited=None):
    """Walk nextId from head_id. Returns (ordered_ids, cycle_detected)."""
    visited = visited if visited is not None else set()
    order = []
    cur = head_id
    while cur:
        if cur in visited:
            return order, True
        visited.add(cur)
        order.append(cur)
        enc = encounters_by_id.get(cur)
        if not isinstance(enc, dict):
            break
        cur = enc.get("nextId")
    return order, False


class RuleDDF00087(RuleTemplate):
    """
    DDF00087: Encounter ordering using previous and next attributes is expected to be consistent with the order of corresponding scheduled activity instances according to their specified default conditions.

    Applies to: Encounter
    Attributes: previousId, nextId
    """

    def __init__(self):
        super().__init__(
            "DDF00087",
            RuleTemplate.WARNING,
            "Encounter ordering using previous and next attributes is expected to be consistent with the order of corresponding scheduled activity instances according to their specified default conditions.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in STUDY_DESIGN_KLASSES:
            for design in data.instances_by_klass(klass):
                encounters = [
                    e for e in design.get("encounters") or [] if isinstance(e, dict)
                ]
                if not encounters:
                    continue
                encounters_by_id = {e.get("id"): e for e in encounters if e.get("id")}
                design_encounter_ids = set(encounters_by_id)

                # (A) Encounter linked-list order
                heads = [e.get("id") for e in encounters if not e.get("previousId")]
                if len(heads) > 1:
                    self._add_failure(
                        f"StudyDesign has {len(heads)} encounter chain heads (previousId=null) — expected 1",
                        "Encounter",
                        "previousId",
                        data.path_by_id(design["id"]),
                    )
                if not heads:
                    continue
                order_a, cycle_a = _walk_encounter_chain(encounters_by_id, heads[0])
                if cycle_a:
                    self._add_failure(
                        "Cycle detected while walking Encounter prev/next chain",
                        "Encounter",
                        "nextId",
                        data.path_by_id(design["id"]),
                    )

                # (B) SAI flow in the main timeline
                timelines = [
                    t
                    for t in design.get("scheduleTimelines") or []
                    if isinstance(t, dict) and t.get("mainTimeline")
                ]
                for timeline in timelines:
                    if not timeline.get("entryId"):
                        continue
                    # Issue 89: walk through decisions as well as activity
                    # instances, and compare only the encounters the walk meets —
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
                            s.get("encounterId")
                            for s in walked
                            if s.get("encounterId") in design_encounter_ids
                        ]
                    )
                    met = set(order_b)
                    chain = [x for x in order_a if x in met]
                    if chain != order_b:
                        self._add_failure(
                            f"Encounter prev/next order {chain} does not match order derived from SAI flow {order_b}",
                            "Encounter",
                            "previousId, nextId",
                            data.path_by_id(timeline["id"]),
                        )
        return self._result()
