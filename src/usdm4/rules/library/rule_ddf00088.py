# MANUAL: do not regenerate
#
# Structural twin of DDF00087 with `epochs` replacing `encounters`
# and `epochId` replacing `encounterId`. Per main ScheduleTimeline,
# compare:
#   A. StudyDesign.epochs linked-list (prev/next starting from
#      previousId=null head).
#   B. SAI flow: walk defaultConditionId from timeline.entryId,
#      collect each SAI's epochId that belongs to this design,
#      dedupe consecutive repeats.
# Flag A != B. Also flag multiple chain heads and cycles.
from usdm4.rules.rule_template import RuleTemplate


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


def _dedupe_consecutive(seq):
    out = []
    for item in seq:
        if not out or out[-1] != item:
            out.append(item)
    return out


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
                    entry_id = timeline.get("entryId")
                    if not entry_id:
                        continue
                    sais = [
                        s
                        for s in timeline.get("instances") or []
                        if isinstance(s, dict)
                        and s.get("instanceType") == "ScheduledActivityInstance"
                    ]
                    sais_by_id = {s.get("id"): s for s in sais if s.get("id")}
                    sai_order, cycle_b = _walk_chain(
                        sais_by_id, entry_id, "defaultConditionId"
                    )
                    if cycle_b:
                        self._add_failure(
                            "Cycle detected while walking ScheduledActivityInstance defaultConditionId chain",
                            "ScheduledActivityInstance",
                            "defaultConditionId",
                            data.path_by_id(timeline["id"]),
                        )
                    order_b_raw = [
                        sais_by_id[sid].get("epochId")
                        for sid in sai_order
                        if sid in sais_by_id
                        and sais_by_id[sid].get("epochId") in design_epoch_ids
                    ]
                    order_b = _dedupe_consecutive(order_b_raw)

                    if order_a != order_b:
                        self._add_failure(
                            f"StudyEpoch prev/next order {order_a} does not match order derived from SAI flow {order_b}",
                            "StudyEpoch",
                            "previousId, nextId",
                            data.path_by_id(timeline["id"]),
                        )
        return self._result()
