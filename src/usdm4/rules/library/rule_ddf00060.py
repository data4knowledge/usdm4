from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00060(RuleTemplate):
    """
    DDF00060: The value for each timing must be a non-negative duration specified in ISO 8601 format.

    Applies to: Timing
    Attributes: value
    """

    def __init__(self):
        super().__init__(
            "DDF00060",
            RuleTemplate.ERROR,
            "The value for each timing must be a non-negative duration specified in ISO 8601 format.",
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
