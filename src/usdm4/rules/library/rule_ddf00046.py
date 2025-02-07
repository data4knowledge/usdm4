from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00046(RuleTemplate):
    """
    DDF00046: A timing must only be specified as being relative to/from a scheduled activity/decision instance that is defined within the same timeline as the timing.

    Applies to: Timing
    Attributes: relativeFromScheduledInstance, relativeToScheduledInstance
    """

    def __init__(self):
        super().__init__(
            "DDF00046",
            RuleTemplate.ERROR,
            "A timing must only be specified as being relative to/from a scheduled activity/decision instance that is defined within the same timeline as the timing.",
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
