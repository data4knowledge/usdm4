from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00026(RuleTemplate):
    """
    DDF00026: A scheduled activity instance must not point (via the \"timeline\" relationship) to the timeline in which it is specified.

    Applies to: ScheduledActivityInstance
    Attributes: timeline
    """

    def __init__(self):
        super().__init__(
            "DDF00026",
            RuleTemplate.ERROR,
            'A scheduled activity instance must not point (via the "timeline" relationship) to the timeline in which it is specified.',
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
