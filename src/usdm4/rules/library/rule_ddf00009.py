# MANUAL: do not regenerate
#
# Each ScheduleTimeline must contain at least one "anchor" — a
# ScheduledActivityInstance in this timeline's `instances` list that is
# referenced (via `relativeToScheduledInstanceId`) by a Timing of type
# "Fixed Reference" (C201358) within this timeline's `timings` list.
#
# Previous implementation had two bugs:
#   - wrong class name: iterated "ScheduledTimeline" (the class is
#     `ScheduleTimeline`), so the outer loop never ran and the rule
#     always passed vacuously;
#   - did not verify that the fixed-reference target actually resolved
#     to one of the timeline's own instances — so a Fixed Reference
#     pointing elsewhere would still pass.
# CORE-000868's failure modes (any of: no fixed refs anywhere, no
# instances in timeline, or no overlap between the two sets) are now
# all caught.
from usdm4.rules.rule_template import RuleTemplate


FIXED_REFERENCE_CODE = "C201358"  # CDISC: Fixed Reference Timing Type
FIXED_REFERENCE_DECODE = "Fixed Reference"  # submission value fallback


def _is_fixed_reference_timing(timing: dict) -> bool:
    if not isinstance(timing, dict):
        return False
    ttype = timing.get("type") or {}
    if not isinstance(ttype, dict):
        return False
    if ttype.get("code") == FIXED_REFERENCE_CODE:
        return True
    # Fall back on decode in case a sample uses the submission value.
    return ttype.get("decode") == FIXED_REFERENCE_DECODE


class RuleDDF00009(RuleTemplate):
    """
    DDF00009: Each schedule timeline must contain at least one anchor (fixed time) - i.e., at least one scheduled activity instance that is referenced by a Fixed Reference timing.

    Applies to: Timing
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00009",
            RuleTemplate.ERROR,
            "Each schedule timeline must contain at least one anchor (fixed time) - i.e., at least one scheduled activity instance that is referenced by a Fixed Reference timing.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for timeline in data.instances_by_klass("ScheduleTimeline"):
            instances = timeline.get("instances") or []
            instance_ids = {
                inst.get("id") for inst in instances if isinstance(inst, dict)
            }
            timings = timeline.get("timings") or []
            fixed_ref_targets = {
                t.get("relativeToScheduledInstanceId")
                for t in timings
                if _is_fixed_reference_timing(t)
            }
            fixed_ref_targets.discard(None)
            if not (fixed_ref_targets & instance_ids):
                self._add_failure(
                    "ScheduleTimeline has no anchor — no instance is the "
                    "target of a Fixed Reference timing within this timeline",
                    "ScheduleTimeline",
                    "timings.type, instances",
                    data.path_by_id(timeline["id"]),
                )
        return self._result()
