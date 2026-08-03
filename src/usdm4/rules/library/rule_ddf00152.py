# MANUAL: do not regenerate
#
# Activity.timelineId must resolve to a ScheduleTimeline living
# under the same StudyDesign as the Activity.
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_KLASSES = [
    "StudyDesign",
    "InterventionalStudyDesign",
    "ObservationalStudyDesign",
]


class RuleDDF00152(RuleTemplate):
    """
    DDF00152: An activity must only reference timelines that are specified within the same study design.

    Applies to: Activity
    Attributes: timelineId
    """

    def __init__(self):
        super().__init__(
            "DDF00152",
            RuleTemplate.ERROR,
            "An activity must only reference timelines that are specified within the same study design.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for activity in data.instances_by_klass("Activity"):
            timeline_id = activity.get("timelineId")
            if not timeline_id:
                continue
            act_design = data.parent_by_klass(activity.get("id"), STUDY_DESIGN_KLASSES)
            tl_design = data.parent_by_klass(timeline_id, STUDY_DESIGN_KLASSES)
            if act_design is None or tl_design is None:
                continue
            if act_design.get("id") != tl_design.get("id"):
                self._add_failure(
                    f"Activity.timelineId {timeline_id!r} is defined under a different StudyDesign",
                    "Activity",
                    "timelineId",
                    data.path_by_id(activity["id"]),
                )
        return self._result()
