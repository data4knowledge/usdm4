# MANUAL: do not regenerate
#
# Cardinality rule: exactly one Primary Objective per StudyDesign. No CORE
# JSONata was provided (the rule isn't in the CORE JSON for v4) — rule text
# is unambiguous. "Primary Objective" is CDISC code C94496 (see
# rule_ddf00096 which uses the same code for the primary objective filter).
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_CLASSES = [
    "StudyDesign",
    "InterventionalStudyDesign",
    "ObservationalStudyDesign",
]
PRIMARY_OBJECTIVE_CODE = "C94496"


class RuleDDF00084(RuleTemplate):
    """
    DDF00084: Within a study design there must be exactly one objective with level 'Primary Objective'.

    Applies to: Objective
    Attributes: level
    """

    def __init__(self):
        super().__init__(
            "DDF00084",
            RuleTemplate.ERROR,
            "Within a study design there must be exactly one objective with level 'Primary Objective'.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sd_cls in STUDY_DESIGN_CLASSES:
            for sd in data.instances_by_klass(sd_cls):
                count = 0
                for obj in sd.get("objectives") or []:
                    level = obj.get("level") or {}
                    if (
                        isinstance(level, dict)
                        and level.get("code") == PRIMARY_OBJECTIVE_CODE
                    ):
                        count += 1
                if count != 1:
                    self._add_failure(
                        f"Expected exactly one Primary Objective in study design, found {count}",
                        sd_cls,
                        "objectives",
                        data.path_by_id(sd["id"]),
                    )
        return self._result()
