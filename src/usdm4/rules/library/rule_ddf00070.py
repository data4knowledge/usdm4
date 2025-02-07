from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00070(RuleTemplate):
    """
    DDF00070: The minimum value of a range must be less than or equal to the maximum value of the range.

    Applies to: Range
    Attributes: minValue, maxValue
    """

    def __init__(self):
        super().__init__(
            "DDF00070",
            RuleTemplate.ERROR,
            "The minimum value of a range must be less than or equal to the maximum value of the range.",
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
