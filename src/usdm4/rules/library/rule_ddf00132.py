from usdm3.rules.library.rule_template import RuleTemplate


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
        """
        Validate the rule against the provided data

        Args:
            config (dict): Standard configuration structure contain the data, CT etc

        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
