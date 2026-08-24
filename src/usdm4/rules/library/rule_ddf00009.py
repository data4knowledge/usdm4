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
from usdm4.rules.timing import is_fixed_reference


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
                if is_fixed_reference(t)
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
