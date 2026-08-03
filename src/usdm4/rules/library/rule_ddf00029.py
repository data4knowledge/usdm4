# MANUAL: do not regenerate
#
# Encounter.previousId / .nextId must resolve to Encounter instances
# living under the same StudyDesign. Twin of DDF00024/28.
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_KLASSES = [
    "StudyDesign",
    "InterventionalStudyDesign",
    "ObservationalStudyDesign",
]


class RuleDDF00029(RuleTemplate):
    """
    DDF00029: An encounter must only reference encounters that are specified within the same study design.

    Applies to: Encounter
    Attributes: previousId, nextId
    """

    def __init__(self):
        super().__init__(
            "DDF00029",
            RuleTemplate.ERROR,
            "An encounter must only reference encounters that are specified within the same study design.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for encounter in data.instances_by_klass("Encounter"):
            enc_design = data.parent_by_klass(encounter.get("id"), STUDY_DESIGN_KLASSES)
            if enc_design is None:
                continue
            for attr in ("previousId", "nextId"):
                target_id = encounter.get(attr)
                if not target_id:
                    continue
                target_design = data.parent_by_klass(target_id, STUDY_DESIGN_KLASSES)
                if target_design is None:
                    continue
                if target_design.get("id") != enc_design.get("id"):
                    self._add_failure(
                        f"Encounter.{attr} {target_id!r} is defined under a different StudyDesign",
                        "Encounter",
                        attr,
                        data.path_by_id(encounter["id"]),
                    )
        return self._result()
