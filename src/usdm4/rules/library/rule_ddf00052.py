from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00052(RuleTemplate):
    """
    DDF00052: All standard code aliases referenced by an instance of the alias code class must be unique.

    Applies to: AliasCode
    Attributes: standardCodeAliases
    """

    def __init__(self):
        super().__init__(
            "DDF00052",
            RuleTemplate.ERROR,
            "All standard code aliases referenced by an instance of the alias code class must be unique.",
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
