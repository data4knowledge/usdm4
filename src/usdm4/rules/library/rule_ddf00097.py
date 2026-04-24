# MANUAL: do not regenerate
#
# Consistency check, not a simple presence check. Same shape as
# DDF00132/DDF00133; see rule_ddf00132.py for the full rationale. The
# previous implementation unconditionally required plannedAge on every
# StudyDesignPopulation, which is stricter than the DDF text and over-
# reports when the value is specified on cohorts instead.
#
# Semantics:
#   pop_has     = population.plannedAge is set
#   cohort_has  = count of cohorts whose plannedAge is set
#   cohort_tot  = total number of cohorts
#
#   FAIL if (pop_has AND cohort_has > 0)
#       — specified in both places
#   FAIL if (NOT pop_has AND 0 < cohort_has < cohort_tot)
#       — specified on only a subset of cohorts
#   PASS otherwise
from usdm4.rules.rule_template import RuleTemplate


ATTR = "plannedAge"


def _is_specified(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict)):
        return bool(value)
    return True


class RuleDDF00097(RuleTemplate):
    """
    DDF00097: Within a study design, the planned age range must be specified either in the study population or in all cohorts.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedAge
    """

    def __init__(self):
        super().__init__(
            "DDF00097",
            RuleTemplate.ERROR,
            "Within a study design, the planned age range must be specified either in the study population or in all cohorts.",
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
