from usdm3.rules.library.rule_template import RuleTemplate


class RuleDDF00058(RuleTemplate):
    """
    DDF00058: Within an indication, if more indication codes are defined, they must be distinct.

    Applies to: Indication
    Attributes: codes
    """

    def __init__(self):
        super().__init__(
            "DDF00058",
            RuleTemplate.ERROR,
            "Within an indication, if more indication codes are defined, they must be distinct.",
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
