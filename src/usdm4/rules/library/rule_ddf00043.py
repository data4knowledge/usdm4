from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00043(RuleTemplate):
    """
    DDF00043: A unit must not be specified for a planned enrollment number or a planned completion number.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedEnrollmentNumber, plannedCompletionNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00043",
            RuleTemplate.ERROR,
            "A unit must not be specified for a planned enrollment number or a planned completion number.",
        )

    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data

        Args:
            config (dict): Standard configuration structure contain the data, CT etc

        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
