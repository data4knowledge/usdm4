# MANUAL: do not regenerate
#
# Note: rule text says "same timeline", not same study design. Timing
# lives under ScheduleTimeline.timings; the referenced SAI lives
# under ScheduleTimeline.instances. Both must share the same
# ScheduleTimeline ancestor.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00046(RuleTemplate):
    """
    DDF00046: A timing must only be specified as being relative to/from a scheduled activity/decision instance that is defined within the same timeline as the timing.

    Applies to: Timing
    Attributes: relativeFromScheduledInstanceId, relativeToScheduledInstanceId
    """

    def __init__(self):
        super().__init__(
            "DDF00046",
            RuleTemplate.ERROR,
            "A timing must only be specified as being relative to/from a scheduled activity/decision instance that is defined within the same timeline as the timing.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for timing in data.instances_by_klass("Timing"):
            timing_tl = data.parent_by_klass(timing.get("id"), "ScheduleTimeline")
            if timing_tl is None:
                continue
            for attr in (
                "relativeFromScheduledInstanceId",
                "relativeToScheduledInstanceId",
            ):
                target_id = timing.get(attr)
                if not target_id:
                    continue
                target_tl = data.parent_by_klass(target_id, "ScheduleTimeline")
                if target_tl is None:
                    continue
                if target_tl.get("id") != timing_tl.get("id"):
                    self._add_failure(
                        f"Timing.{attr} {target_id!r} is defined under a different ScheduleTimeline",
                        "Timing",
                        attr,
                        data.path_by_id(timing["id"]),
                    )
        return self._result()
