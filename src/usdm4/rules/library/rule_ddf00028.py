from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00028(RuleTemplate):
    """
    DDF00028: An activity must only reference activities that are specified within the same study design.

    Applies to: Activity
    Attributes: previous, next
    """

    def __init__(self):
        super().__init__(
            "DDF00028",
            RuleTemplate.ERROR,
            "An activity must only reference activities that are specified within the same study design.",
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
