from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00098(RuleTemplate):
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
        """
        Validate the rule against the provided data

        Args:
            config (dict): Standard configuration structure contain the data, CT etc

        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
