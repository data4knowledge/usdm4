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
        for item in data.instances_by_klass("ScheduleTimeline"):
            if not item.get("$timeline_exits"):
                self._add_failure(
                    "Required attribute '$timeline_exits' is missing or empty",
                    "ScheduleTimeline",
                    "$timeline_exits",
                    data.path_by_id(item["id"]),
                )
        return self._result()
