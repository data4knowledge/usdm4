# MANUAL: do not regenerate
#
# Required consistency check. Unlike DDF00132/DDF00133 ("if a planned
# number is defined …"), DDF00097 has no "if defined" clause — the
# planned age range MUST be specified somewhere. Failure cases:
#   1. Both pop AND some cohort → specified in two places
#   2. pop missing AND only SOME cohorts have it → subset
#   3. pop missing AND NO cohorts have it → not specified anywhere
#      (also catches the no-cohorts case)
# Passes when exactly one axis carries it — pop-only (no cohort overlap),
# or all-cohorts-only (and at least one cohort exists).
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

            path = data.path_by_id(population["id"])

            if pop_has and cohort_has > 0:
                self._add_failure(
                    f"{ATTR} is specified on the study population and on "
                    f"{cohort_has} of {cohort_total} cohort(s); specify it "
                    f"in one place only",
                    "StudyDesignPopulation",
                    ATTR,
                    path,
                )
            elif not pop_has and cohort_total > 0 and 0 < cohort_has < cohort_total:
                self._add_failure(
                    f"{ATTR} is specified on only {cohort_has} of "
                    f"{cohort_total} cohort(s); specify it on all cohorts "
                    f"or on the study population",
                    "StudyDesignPopulation",
                    ATTR,
                    path,
                )
            elif not pop_has and cohort_has == 0:
                self._add_failure(
                    f"{ATTR} is not specified on the study population and "
                    f"not specified on any of the {cohort_total} cohort(s); "
                    f"specify it on the study population or on all cohorts",
                    "StudyDesignPopulation",
                    ATTR,
                    path,
                )
        return self._result()
