# MANUAL: do not regenerate
#
# SAIs in the main timeline must name an epoch. The CORE condition
# filters by `mainTimeline = true` on the containing ScheduleTimeline;
# we walk up to the parent ScheduleTimeline via parent_by_klass.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00080(RuleTemplate):
    """
    DDF00080: All scheduled activity instances are expected to refer to an epoch.

    Applies to: ScheduledActivityInstance (main-timeline only)
    Attributes: epochId
    """

    def __init__(self):
        super().__init__(
            "DDF00080",
            RuleTemplate.WARNING,
            "All scheduled activity instances are expected to refer to an epoch.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sai in data.instances_by_klass("ScheduledActivityInstance"):
            timeline = data.parent_by_klass(sai.get("id"), "ScheduleTimeline")
            if not isinstance(timeline, dict) or not timeline.get("mainTimeline"):
                continue
            if not sai.get("epochId"):
                self._add_failure(
                    "ScheduledActivityInstance in the main timeline does not refer to an epoch",
                    "ScheduledActivityInstance",
                    "epochId",
                    data.path_by_id(sai["id"]),
                )
        return self._result()
