from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00050(RuleTemplate):
    """
    DDF00050: A study arm must only reference study populations or cohorts that are defined within the same study design as the study arm.

    Applies to: StudyArm
    Attributes: populations
    """

    def __init__(self):
        super().__init__(
            "DDF00050",
            RuleTemplate.ERROR,
            "A study arm must only reference study populations or cohorts that are defined within the same study design as the study arm.",
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
