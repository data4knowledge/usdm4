# MANUAL: do not regenerate
#
# Required consistency check. See rule_ddf00097.py for the full rationale
# of why the "nothing specified anywhere" case is a failure here (no
# "if defined" clause in the DDF text) but not in DDF00132/DDF00133.
from usdm4.rules.rule_template import RuleTemplate


ATTR = "plannedSex"


def _is_specified(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict)):
        return bool(value)
    return True


class RuleDDF00098(RuleTemplate):
    """
    DDF00098: Within a study design, the planned sex must be specified either in the study population or in all cohorts.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedSex
    """

    def __init__(self):
        super().__init__(
            "DDF00098",
            RuleTemplate.ERROR,
            "Within a study design, the planned sex must be specified either in the study population or in all cohorts.",
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
