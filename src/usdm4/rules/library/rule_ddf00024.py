# MANUAL: do not regenerate
#
# StudyEpoch.previousId / .nextId must resolve to StudyEpoch instances
# that live under the same StudyDesign. Pattern from DDF00107/00127.
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_KLASSES = ["StudyDesign", "InterventionalStudyDesign", "ObservationalStudyDesign"]


class RuleDDF00024(RuleTemplate):
    """
    DDF00024: An epoch must only reference epochs that are specified within the same study design.

    Applies to: StudyEpoch
    Attributes: previousId, nextId
    """

    def __init__(self):
        super().__init__(
            "DDF00024",
            RuleTemplate.ERROR,
            "An epoch must only reference epochs that are specified within the same study design.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for epoch in data.instances_by_klass("StudyEpoch"):
            epoch_design = data.parent_by_klass(epoch.get("id"), STUDY_DESIGN_KLASSES)
            if epoch_design is None:
                continue
            for attr in ("previousId", "nextId"):
                target_id = epoch.get(attr)
                if not target_id:
                    continue
                target_design = data.parent_by_klass(target_id, STUDY_DESIGN_KLASSES)
                if target_design is None:
                    continue
                if target_design.get("id") != epoch_design.get("id"):
                    self._add_failure(
                        f"StudyEpoch.{attr} {target_id!r} is defined under a different StudyDesign",
                        "StudyEpoch",
                        attr,
                        data.path_by_id(epoch["id"]),
                    )
        return self._result()
