from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00129(RuleTemplate):
    """
    DDF00129: A study intervention's product designation must be specified using the product designation (C207418) DDF codelist.

    Applies to: StudyIntervention
    Attributes: productDesignation
    """

    def __init__(self):
        super().__init__(
            "DDF00129",
            RuleTemplate.ERROR,
            "A study intervention's product designation must be specified using the product designation (C207418) DDF codelist.",
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
