# MANUAL: do not regenerate
#
# SAI's `timelineId` (its sub-timeline pointer) must not equal the id
# of the ScheduleTimeline that contains it. Walk up to the parent
# timeline and compare.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00026(RuleTemplate):
    """
    DDF00026: A scheduled activity instance must not point (via the "timeline" relationship) to the timeline in which it is specified.

    Applies to: ScheduledActivityInstance
    Attributes: timelineId
    """

    def __init__(self):
        super().__init__(
            "DDF00026",
            RuleTemplate.ERROR,
            'A scheduled activity instance must not point (via the "timeline" relationship) to the timeline in which it is specified.',
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sai in data.instances_by_klass("ScheduledActivityInstance"):
            sub_timeline_id = sai.get("timelineId")
            if not sub_timeline_id:
                continue
            parent_timeline = data.parent_by_klass(sai.get("id"), "ScheduleTimeline")
            if not isinstance(parent_timeline, dict):
                continue
            if sub_timeline_id == parent_timeline.get("id"):
                self._add_failure(
                    "ScheduledActivityInstance's sub-timeline points to its own containing timeline",
                    "ScheduledActivityInstance",
                    "timelineId",
                    data.path_by_id(sai["id"]),
                )
        return self._result()
