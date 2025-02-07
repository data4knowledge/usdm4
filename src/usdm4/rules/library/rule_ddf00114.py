from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00114(RuleTemplate):
    """
    DDF00114: If specified, the context of a condition must point to a valid instance in the activity or scheduled activity instance class.

    Applies to: Condition
    Attributes: context
    """

    def __init__(self):
        super().__init__(
            "DDF00114",
            RuleTemplate.ERROR,
            "If specified, the context of a condition must point to a valid instance in the activity or scheduled activity instance class.",
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
