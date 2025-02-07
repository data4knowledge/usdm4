from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00105(RuleTemplate):
    """
    DDF00105: A scheduled activity/decision instance must only reference an epoch that is defined within the same study design as the scheduled activity/decision instance.

    Applies to: ScheduledActivityInstance, ScheduledDecisionInstance
    Attributes: epoch
    """

    def __init__(self):
        super().__init__(
            "DDF00105",
            RuleTemplate.ERROR,
            "A scheduled activity/decision instance must only reference an epoch that is defined within the same study design as the scheduled activity/decision instance.",
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
