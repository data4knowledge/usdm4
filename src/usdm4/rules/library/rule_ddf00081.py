from usdm3.rules.library.rule_template import RuleTemplate


class RuleDDF00081(RuleTemplate):
    """
    DDF00081: Class relationships must conform with the USDM schema based on the API specification.

    Applies to: All
    Attributes: All
    """

    def __init__(self):
        super().__init__(
            "DDF00081",
            RuleTemplate.ERROR,
            "Class relationships must conform with the USDM schema based on the API specification.",
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
