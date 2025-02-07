from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00113(RuleTemplate):
    """
    DDF00113: An agent administration's frequency must be specified according to the extensible Frequency (C71113) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: AgentAdministration
    Attributes: frequency
    """

    def __init__(self):
        super().__init__(
            "DDF00113",
            RuleTemplate.ERROR,
            "An agent administration's frequency must be specified according to the extensible Frequency (C71113) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
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
