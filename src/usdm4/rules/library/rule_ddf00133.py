# MANUAL: do not regenerate
#
# Sibling of DDF00132 — same consistency check but for
# plannedEnrollmentNumber. See rule_ddf00132.py for the full rationale;
# semantics reconciled against CORE-000963.
from usdm4.rules.rule_template import RuleTemplate


ATTR = "plannedEnrollmentNumber"


def _is_specified(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict)):
        return bool(value)
    return True


class RuleDDF00133(RuleTemplate):
    """
    DDF00133: Within a study design, if a planned enrollment number is defined, it must be specified either in the study population or in all cohorts.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedEnrollmentNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00133",
            RuleTemplate.ERROR,
            "Within a study design, if a planned enrollment number is defined, it must be specified either in the study population or in all cohorts.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for population in data.instances_by_klass("StudyDesignPopulation"):
            pop_has = _is_specified(population.get(ATTR))
            cohorts = population.get("cohorts") or []
            cohort_total = len(cohorts)
            cohort_has = sum(
                1 for c in cohorts if isinstance(c, dict) and _is_specified(c.get(ATTR))
            )

            if pop_has and cohort_has > 0:
                self._add_failure(
                    f"{ATTR} is specified on the study population and on "
                    f"{cohort_has} of {cohort_total} cohort(s); specify it "
                    f"in one place only",
                    "StudyDesignPopulation",
                    ATTR,
                    data.path_by_id(population["id"]),
                )
            elif not pop_has and 0 < cohort_has < cohort_total:
                self._add_failure(
                    f"{ATTR} is specified on only {cohort_has} of "
                    f"{cohort_total} cohort(s); specify it on all cohorts "
                    f"or on the study population",
                    "StudyDesignPopulation",
                    ATTR,
                    data.path_by_id(population["id"]),
                )
        return self._result()
