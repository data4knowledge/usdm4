# MANUAL: do not regenerate
#
# Applied to both StudyDesignPopulation and StudyCohort. Previous
# implementation returned `pop_result or cohort_result` — if the population
# side passed (returned True) but the cohort side raised failures, the rule
# reported Success because True or False → True, hiding accumulated errors.
# Both `_ct_check` calls run unconditionally so all failures are collected
# on `self._errors`; the final status must come from `self._result()`.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00141(RuleTemplate):
    """
    DDF00141: A planned sex must be specified using the Sex of Participants (C66732) SDTM codelist.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedSex
    """

    def __init__(self):
        super().__init__(
            "DDF00141",
            RuleTemplate.ERROR,
            "A planned sex must be specified using the Sex of Participants (C66732) SDTM codelist.",
        )

    def validate(self, config: dict) -> bool:
        self._ct_check(config, "StudyDesignPopulation", "plannedSex")
        self._ct_check(config, "StudyCohort", "plannedSex")
        return self._result()
