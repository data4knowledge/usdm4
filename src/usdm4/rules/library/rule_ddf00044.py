from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00044(RuleTemplate):
    """
    DDF00044: The target for a condition must not be equal to its parent.

    Applies to: ConditionAssignment
    Attributes: conditionTarget
    """

    def __init__(self):
        super().__init__(
            "DDF00044",
            RuleTemplate.ERROR,
            "The target for a condition must not be equal to its parent.",
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
