from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00025(RuleTemplate):
    """
    DDF00025: A window must not be defined for an anchor timing (i.e., type is \"Fixed Reference\").

    Applies to: Timing
    Attributes: windowLabel, windowLower, windowUpper
    """

    def __init__(self):
        super().__init__(
            "DDF00025",
            RuleTemplate.ERROR,
            'A window must not be defined for an anchor timing (i.e., type is "Fixed Reference").',
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
