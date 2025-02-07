from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00011(RuleTemplate):
    """
    DDF00011: Anchor timings (e.g. type is \"Fixed Reference\") must be related to a scheduled activity instance via a relativeFromScheduledInstance relationship.

    Applies to: Timing
    Attributes: relativeFromScheduledInstance
    """

    def __init__(self):
        super().__init__(
            "DDF00011",
            RuleTemplate.ERROR,
            'Anchor timings (e.g. type is "Fixed Reference") must be related to a scheduled activity instance via a relativeFromScheduledInstance relationship.',
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
