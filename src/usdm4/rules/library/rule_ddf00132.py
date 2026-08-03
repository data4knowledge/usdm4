# MANUAL: do not regenerate
#
# Consistency check, not a simple presence check. The previous
# implementation unconditionally required plannedCompletionNumber on
# every StudyDesignPopulation, which is stricter than the DDF text and
# disagrees with CORE-000962.
#
# The correct semantics (reconciled from the DDF text plus CORE's JSONata
# `check` formula):
#   pop_has     = population.plannedCompletionNumber is set
#   cohort_has  = count of cohorts whose plannedCompletionNumber is set
#   cohort_tot  = total number of cohorts
#
#   FAIL if (pop_has AND cohort_has > 0)
#       — "specified for both the population and one or more cohorts"
#   FAIL if (NOT pop_has AND 0 < cohort_has < cohort_tot)
#       — "specified for only a subset of the cohorts"
#   PASS otherwise (population-only, all-cohorts-only, or nowhere defined)
from usdm4.rules.rule_template import RuleTemplate


ATTR = "plannedCompletionNumber"


def _is_specified(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict)):
        return bool(value)
    return True


class RuleDDF00132(RuleTemplate):
    """
    DDF00132: Within a study design, if a planned completion number is defined, it must be specified either in the study population or in all cohorts.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedCompletionNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00132",
            RuleTemplate.ERROR,
            "Within a study design, if a planned completion number is defined, it must be specified either in the study population or in all cohorts.",
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
