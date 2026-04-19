# MANUAL: do not regenerate
#
# Every ScheduleTimeline with mainTimeline=true must have a non-empty
# plannedDuration (embedded Duration).
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00153(RuleTemplate):
    """
    DDF00153: A planned duration is expected for the main timeline.

    Applies to: ScheduleTimeline (mainTimeline only)
    Attributes: plannedDuration
    """

    def __init__(self):
        super().__init__(
            "DDF00153",
            RuleTemplate.WARNING,
            "A planned duration is expected for the main timeline.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for timeline in data.instances_by_klass("ScheduleTimeline"):
            if not timeline.get("mainTimeline"):
                continue
            if not timeline.get("plannedDuration"):
                self._add_failure(
                    "Main ScheduleTimeline has no plannedDuration",
                    "ScheduleTimeline",
                    "plannedDuration",
                    data.path_by_id(timeline["id"]),
                )
        return self._result()
