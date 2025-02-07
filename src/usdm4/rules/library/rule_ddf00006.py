from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00006(RuleTemplate):
    """
    DDF00006: Timing windows must be fully defined, if one of the window attributes (i.e., window label, window lower, and window upper) is defined then all must be specified.

    Applies to: Timing
    Attributes: windowLabel, windowLower, windowUpper
    """

    def __init__(self):
        super().__init__(
            "DDF00006",
            RuleTemplate.ERROR,
            "Timing windows must be fully defined, if one of the window attributes (i.e., window label, window lower, and window upper) is defined then all must be specified.",
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
