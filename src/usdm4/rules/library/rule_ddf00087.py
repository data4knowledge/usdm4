# MANUAL: do not regenerate
#
# Compare two encounter orderings per main ScheduleTimeline:
#   A. Linked-list walk of StudyDesign.encounters via prev/next
#      (start from the encounter with previousId=null, follow nextId).
#   B. SAI flow: start at ScheduleTimeline.entryId, follow
#      defaultConditionId links, collect each SAI's encounterId that
#      belongs to this StudyDesign, dedupe consecutive repeats.
# Flag when A != B. Additionally flag:
#   - multiple encounter heads (>1 encounter with previousId=null)
#   - cycles detected in either walk (visited-set guard)
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_KLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]


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


def _walk_sai_chain(sais_by_id, entry_id):
    """Walk defaultConditionId from entry_id. Returns (ordered_sai_ids, cycle_detected)."""
    visited: set = set()
    order = []
    cur = entry_id
    while cur:
        if cur in visited:
            return order, True
        visited.add(cur)
        order.append(cur)
        sai = sais_by_id.get(cur)
        if not isinstance(sai, dict):
            break
        cur = sai.get("defaultConditionId")
    return order, False


def _dedupe_consecutive(seq):
    out = []
    for item in seq:
        if not out or out[-1] != item:
            out.append(item)
    return out


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
                encounters = [e for e in design.get("encounters") or [] if isinstance(e, dict)]
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
                    t for t in design.get("scheduleTimelines") or []
                    if isinstance(t, dict) and t.get("mainTimeline")
                ]
                for timeline in timelines:
                    entry_id = timeline.get("entryId")
                    if not entry_id:
                        continue
                    sais = [
                        s for s in timeline.get("instances") or []
                        if isinstance(s, dict)
                        and s.get("instanceType") == "ScheduledActivityInstance"
                    ]
                    sais_by_id = {s.get("id"): s for s in sais if s.get("id")}
                    sai_order, cycle_b = _walk_sai_chain(sais_by_id, entry_id)
                    if cycle_b:
                        self._add_failure(
                            "Cycle detected while walking ScheduledActivityInstance defaultConditionId chain",
                            "ScheduledActivityInstance",
                            "defaultConditionId",
                            data.path_by_id(timeline["id"]),
                        )
                    order_b_raw = [
                        sais_by_id[sid].get("encounterId")
                        for sid in sai_order
                        if sid in sais_by_id
                        and sais_by_id[sid].get("encounterId") in design_encounter_ids
                    ]
                    order_b = _dedupe_consecutive(order_b_raw)

                    if order_a != order_b:
                        self._add_failure(
                            f"Encounter prev/next order {order_a} does not match order derived from SAI flow {order_b}",
                            "Encounter",
                            "previousId, nextId",
                            data.path_by_id(timeline["id"]),
                        )
        return self._result()
