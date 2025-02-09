from usdm3.rules.library.rule_template import RuleTemplate


class RuleDDF00073(RuleTemplate):
    """
    DDF00073: Only one version of any code system is expected to be used within a study version.

    Applies to: Code
    Attributes: codeSystemVersion
    """

    def __init__(self):
        super().__init__(
            "DDF00073",
            RuleTemplate.ERROR,
            "Only one version of any code system is expected to be used within a study version.",
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
