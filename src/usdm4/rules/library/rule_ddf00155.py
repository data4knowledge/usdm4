from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00155(RuleTemplate):
    """
    DDF00155: For CDISC codelist references (where the code system is 'http://www.cdisc.org'), the code system version must be a valid CDISC terminology release date in ISO 8601 date format.

    Applies to: Code
    Attributes: codeSystemVersion
    """

    def __init__(self):
        super().__init__(
            "DDF00155",
            RuleTemplate.ERROR,
            "For CDISC codelist references (where the code system is 'http://www.cdisc.org'), the code system version must be a valid CDISC terminology release date in ISO 8601 date format.",
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
