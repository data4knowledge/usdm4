from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00051(RuleTemplate):
    """
    DDF00051: A timing's type must be specified using the Timing Type Value Set Terminology (C201264) DDF codelist.

    Applies to: Timing
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00051",
            RuleTemplate.ERROR,
            "A timing's type must be specified using the Timing Type Value Set Terminology (C201264) DDF codelist.",
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
