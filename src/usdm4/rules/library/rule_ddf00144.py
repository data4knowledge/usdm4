from usdm3.rules.library.rule_template import RuleTemplate


class RuleDDF00144(RuleTemplate):
    """
    DDF00144: A study geographic scope type must be specified using the geographic scope type (C207412) DDF codelist.

    Applies to: GeographicScope
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00144",
            RuleTemplate.ERROR,
            "A study geographic scope type must be specified using the geographic scope type (C207412) DDF codelist.",
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
