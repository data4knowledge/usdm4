# MANUAL: do not regenerate
#
# Activity.previousId / .nextId must resolve to Activity instances
# living under the same StudyDesign. Twin of DDF00024/29.
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_KLASSES = [
    "StudyDesign",
    "InterventionalStudyDesign",
    "ObservationalStudyDesign",
]


class RuleDDF00028(RuleTemplate):
    """
    DDF00028: An activity must only reference activities that are specified within the same study design.

    Applies to: Activity
    Attributes: previousId, nextId
    """

    def __init__(self):
        super().__init__(
            "DDF00028",
            RuleTemplate.ERROR,
            "An activity must only reference activities that are specified within the same study design.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for activity in data.instances_by_klass("Activity"):
            act_design = data.parent_by_klass(activity.get("id"), STUDY_DESIGN_KLASSES)
            if act_design is None:
                continue
            for attr in ("previousId", "nextId"):
                target_id = activity.get(attr)
                if not target_id:
                    continue
                target_design = data.parent_by_klass(target_id, STUDY_DESIGN_KLASSES)
                if target_design is None:
                    continue
                if target_design.get("id") != act_design.get("id"):
                    self._add_failure(
                        f"Activity.{attr} {target_id!r} is defined under a different StudyDesign",
                        "Activity",
                        attr,
                        data.path_by_id(activity["id"]),
                    )
        return self._result()
