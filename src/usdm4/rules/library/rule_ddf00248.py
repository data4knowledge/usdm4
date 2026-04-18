# MANUAL: do not regenerate
#
# Uniqueness within scope: an EligibilityCriterionItem (referenced by
# EligibilityCriterion.criterionItemId) must not be used more than once
# within the same study design. CORE JSONata groups by
# (studyDesign.id, criterionItemId).
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_CLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]


class RuleDDF00248(RuleTemplate):
    """
    DDF00248: An eligibility criterion item must not be used more than once within a study design.

    Applies to: EligibilityCriterion
    Attributes: criterionItem
    """

    def __init__(self):
        super().__init__(
            "DDF00248",
            RuleTemplate.ERROR,
            "An eligibility criterion item must not be used more than once within a study design.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sd_cls in STUDY_DESIGN_CLASSES:
            for sd in data.instances_by_klass(sd_cls):
                seen: dict = {}
                for ec in sd.get("eligibilityCriteria") or []:
                    if not isinstance(ec, dict):
                        continue
                    item_id = ec.get("criterionItemId")
                    if item_id in (None, ""):
                        continue
                    if item_id in seen:
                        self._add_failure(
                            f"EligibilityCriterionItem {item_id!r} is referenced by more than one EligibilityCriterion in this study design",
                            "EligibilityCriterion",
                            "criterionItemId",
                            data.path_by_id(ec["id"]),
                        )
                    else:
                        seen[item_id] = ec["id"]
        return self._result()
