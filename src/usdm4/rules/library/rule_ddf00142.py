from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00142(RuleTemplate):
    """
    DDF00142: A governance date type must be specified according to the extensible governance date type (C207413) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: GovernanceDate
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00142",
            RuleTemplate.ERROR,
            "A governance date type must be specified according to the extensible governance date type (C207413) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
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
