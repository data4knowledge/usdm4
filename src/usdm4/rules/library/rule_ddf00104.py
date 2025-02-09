from usdm3.rules.library.rule_template import RuleTemplate


class RuleDDF00104(RuleTemplate):
    """
    DDF00104: A timing's relative to/from property must be specified using the Timing Relative To From Value Set Terminology (C201265) SDTM codelist.

    Applies to: Timing
    Attributes: relativeToFrom
    """

    def __init__(self):
        super().__init__(
            "DDF00104",
            RuleTemplate.ERROR,
            "A timing's relative to/from property must be specified using the Timing Relative To From Value Set Terminology (C201265) SDTM codelist.",
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
