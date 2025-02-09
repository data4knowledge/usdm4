from usdm3.rules.library.rule_template import RuleTemplate


class RuleDDF00029(RuleTemplate):
    """
    DDF00029: An encounter must only reference encounters that are specified within the same study design.

    Applies to: Encounter
    Attributes: previous, next
    """

    def __init__(self):
        super().__init__(
            "DDF00029",
            RuleTemplate.ERROR,
            "An encounter must only reference encounters that are specified within the same study design.",
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
