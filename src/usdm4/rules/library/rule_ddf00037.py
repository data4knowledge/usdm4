# MANUAL: do not regenerate
#
# Auto-classified as HIGH_REQUIRED_ATTRIBUTE by stage-1 (rule text matched the
# "at least one ... must" idiom) but the semantic is set-level, not
# per-instance: for each ScheduleTimeline, at least ONE of its
# ScheduledActivityInstances must have a timelineExitId set. Hand-authored.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00037(RuleTemplate):
    """
    DDF00037: At least one scheduled activity instance within a timeline must point to a timeline exit.

    Applies to: ScheduledActivityInstance
    Attributes: timelineExit
    """

    def __init__(self):
        super().__init__(
            "DDF00037",
            RuleTemplate.ERROR,
            "At least one scheduled activity instance within a timeline must point to a timeline exit.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for timeline in data.instances_by_klass("ScheduleTimeline"):
            activities = [
                sai for sai in data.instances_by_klass("ScheduledActivityInstance")
                if (p := data.parent_by_klass(sai["id"], ["ScheduleTimeline"])) is not None
                and p["id"] == timeline["id"]
            ]
            if not activities:
                # A timeline without any activity instances can't satisfy the
                # rule by definition; leave that as a separate concern.
                continue
            if not any(sai.get("timelineExitId") for sai in activities):
                self._add_failure(
                    "No scheduled activity instance in this timeline points to a timeline exit",
                    "ScheduleTimeline",
                    "timelineExitId",
                    data.path_by_id(timeline["id"]),
                )
        return self._result()
