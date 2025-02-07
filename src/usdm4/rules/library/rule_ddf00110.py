from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00110(RuleTemplate):
    """
    DDF00110: An eligibility criterion's category must be specified using the Category of Inclusion/Exclusion (C66797) SDTM codelist.

    Applies to: EligibilityCriterion
    Attributes: category
    """

    def __init__(self):
        super().__init__(
            "DDF00110",
            RuleTemplate.ERROR,
            "An eligibility criterion's category must be specified using the Category of Inclusion/Exclusion (C66797) SDTM codelist.",
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
