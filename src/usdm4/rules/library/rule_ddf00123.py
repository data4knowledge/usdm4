from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00123(RuleTemplate):
    """
    DDF00123: A masking role must be specified according to the extensible masking role (C207414) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: Masking
    Attributes: role
    """

    def __init__(self):
        super().__init__(
            "DDF00123",
            RuleTemplate.ERROR,
            "A masking role must be specified according to the extensible masking role (C207414) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
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
