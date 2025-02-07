from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00064(RuleTemplate):
    """
    DDF00064: A scheduled decision instance is not expected to refer to a timeline exit.

    Applies to: ScheduledDecisionInstance
    Attributes: timelineExit
    """

    def __init__(self):
        super().__init__(
            "DDF00064",
            RuleTemplate.ERROR,
            "A scheduled decision instance is not expected to refer to a timeline exit.",
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
