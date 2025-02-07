from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00036(RuleTemplate):
    """
    DDF00036: If timing type is \"Fixed Reference\" then the corresponding attribute relativeToFrom must be filled with \"Start to Start\".

    Applies to: Timing
    Attributes: relativeToFrom
    """

    def __init__(self):
        super().__init__(
            "DDF00036",
            RuleTemplate.ERROR,
            'If timing type is "Fixed Reference" then the corresponding attribute relativeToFrom must be filled with "Start to Start".',
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
