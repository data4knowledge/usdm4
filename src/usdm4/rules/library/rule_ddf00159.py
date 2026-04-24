# MANUAL: do not regenerate
#
# An EligibilityCriterion must not be referenced by both a study design
# population AND any cohort of the same study design population. CORE JSONata:
#   $s.eligibilityCriteria[id in $s.population.criterionIds and
#                          id in $s.population.cohorts.criterionIds]
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_CLASSES = ["StudyDesign", "InterventionalStudyDesign", "ObservationalStudyDesign"]


class RuleDDF00159(RuleTemplate):
    """
    DDF00159: An eligibility criterion must not be referenced by both a study design population and any of the cohorts of the same study design population.

    Applies to: ObservationalStudyDesign
    Attributes: criteria
    """

    def __init__(self):
        super().__init__(
            "DDF00159",
            RuleTemplate.ERROR,
            "An eligibility criterion must not be referenced by both a study design population and any of the cohorts of the same study design population.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sd_cls in STUDY_DESIGN_CLASSES:
            for sd in data.instances_by_klass(sd_cls):
                pop = sd.get("population") or {}
                if not isinstance(pop, dict):
                    continue
                pop_ids = set(pop.get("criterionIds") or [])
                cohort_ids: set = set()
                for cohort in pop.get("cohorts") or []:
                    if isinstance(cohort, dict):
                        cohort_ids.update(cohort.get("criterionIds") or [])
                both = pop_ids & cohort_ids
                if not both:
                    continue
                # Report against each offending EligibilityCriterion
                for ec in sd.get("eligibilityCriteria") or []:
                    if isinstance(ec, dict) and ec.get("id") in both:
                        self._add_failure(
                            "EligibilityCriterion is referenced by both the study design population and a cohort",
                            "EligibilityCriterion",
                            "id",
                            data.path_by_id(ec["id"]),
                        )
        return self._result()
