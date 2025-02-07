from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00053(RuleTemplate):
    """
    DDF00053: Within an encounter there must be no duplicate environmental settings.

    Applies to: Encounter
    Attributes: environmentalSetting
    """

    def __init__(self):
        super().__init__(
            "DDF00053",
            RuleTemplate.ERROR,
            "Within an encounter there must be no duplicate environmental settings.",
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
