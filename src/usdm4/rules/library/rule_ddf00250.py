# MANUAL: do not regenerate
#
# For each EligibilityCriterion: if its id is referenced by ANY
# StudyDesignPopulation.criterionIds AND ANY StudyCohort.criterionIds,
# that's a failure. The rule scope lists population/cohort classes but
# the failure is reported against the offending criterion.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00250(RuleTemplate):
    """
    DDF00250: An eligibility criterion must be referenced by either a study design population or cohorts, not both.

    Applies to: EligibilityCriterion (referenced from StudyDesignPopulation, StudyCohort)
    Attributes: criterionIds
    """

    def __init__(self):
        super().__init__(
            "DDF00250",
            RuleTemplate.ERROR,
            "An eligibility criterion must be referenced by either a study design population or cohorts, not both.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        pop_refs: set = set()
        for pop in data.instances_by_klass("StudyDesignPopulation"):
            for cid in pop.get("criterionIds") or []:
                if cid:
                    pop_refs.add(cid)
        cohort_refs: set = set()
        for cohort in data.instances_by_klass("StudyCohort"):
            for cid in cohort.get("criterionIds") or []:
                if cid:
                    cohort_refs.add(cid)
        dual_refs = pop_refs & cohort_refs
        for criterion in data.instances_by_klass("EligibilityCriterion"):
            if criterion.get("id") in dual_refs:
                self._add_failure(
                    "EligibilityCriterion is referenced by both a StudyDesignPopulation and a StudyCohort",
                    "EligibilityCriterion",
                    "criterionIds",
                    data.path_by_id(criterion["id"]),
                )
        return self._result()
