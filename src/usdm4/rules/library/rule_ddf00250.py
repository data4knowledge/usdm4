from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00250(RuleTemplate):
    """
    DDF00250: An eligibility criterion must be referenced by either a study design population or cohorts, not both.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: criteria
    """

    def __init__(self):
        super().__init__(
            "DDF00250",
            RuleTemplate.ERROR,
            "An eligibility criterion must be referenced by either a study design population or cohorts, not both.",
        )

    # TODO: implement. STUB: rule not present in CORE catalogue
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00250: not yet implemented")
