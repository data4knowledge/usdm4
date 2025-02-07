from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00066(RuleTemplate):
    """
    DDF00066: A scheduled decision instance is expected to refer to a default condition.

    Applies to: ScheduledDecisionInstance
    Attributes: defaultCondition
    """

    def __init__(self):
        super().__init__(
            "DDF00066",
            RuleTemplate.ERROR,
            "A scheduled decision instance is expected to refer to a default condition.",
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
