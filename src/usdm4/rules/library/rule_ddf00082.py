from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00082(RuleTemplate):
    """
    DDF00082: Data types of attributes (string, number, boolean) must conform with the USDM schema based on the API specification.

    Applies to: All
    Attributes: All
    """

    def __init__(self):
        super().__init__(
            "DDF00082",
            RuleTemplate.ERROR,
            "Data types of attributes (string, number, boolean) must conform with the USDM schema based on the API specification.",
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
