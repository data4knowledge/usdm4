# MANUAL: do not regenerate
#
# Walks the SAI → its sub-timeline (via timelineId) → parent
# StudyDesign of the sub-timeline vs. parent StudyDesign of the SAI.
# Any mismatch is a failure. Uses parent_by_klass with a multi-class
# list to cover both Interventional and Observational study designs.
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_KLASSES = ["StudyDesign", "InterventionalStudyDesign", "ObservationalStudyDesign"]


class RuleDDF00107(RuleTemplate):
    """
    DDF00107: A scheduled activity instance must only have a sub-timeline that is defined within the same study design as the scheduled activity instance.

    Applies to: ScheduledActivityInstance
    Attributes: timelineId
    """

    def __init__(self):
        super().__init__(
            "DDF00107",
            RuleTemplate.ERROR,
            "A scheduled activity instance must only have a sub-timeline that is defined within the same study design as the scheduled activity instance.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sai in data.instances_by_klass("ScheduledActivityInstance"):
            sub_id = sai.get("timelineId")
            if not sub_id:
                continue
            sub_timeline = data.instance_by_id(sub_id)
            if not isinstance(sub_timeline, dict):
                continue
            sai_design = data.parent_by_klass(sai.get("id"), STUDY_DESIGN_KLASSES)
            sub_design = data.parent_by_klass(sub_id, STUDY_DESIGN_KLASSES)
            if sai_design is None or sub_design is None:
                continue
            if sai_design.get("id") != sub_design.get("id"):
                self._add_failure(
                    f"ScheduledActivityInstance's sub-timeline {sub_id!r} is defined under a different StudyDesign",
                    "ScheduledActivityInstance",
                    "timelineId",
                    data.path_by_id(sai["id"]),
                )
        return self._result()
