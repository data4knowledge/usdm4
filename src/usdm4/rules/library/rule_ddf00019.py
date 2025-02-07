from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00019(RuleTemplate):
    """
    DDF00019: A scheduled activity/decision instance must not refer to itself as its default condition.

    Applies to: ScheduledActivityInstance, ScheduledDecisionInstance
    Attributes: defaultCondition
    """

    def __init__(self):
        super().__init__(
            "DDF00019",
            RuleTemplate.ERROR,
            "A scheduled activity/decision instance must not refer to itself as its default condition.",
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
