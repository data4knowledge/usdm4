from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00140(RuleTemplate):
    """
    DDF00140: An organization type must be specified according to the extensible organization type (C188724) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: Organization, ResearchOrganization
    Attributes: organizationType
    """

    def __init__(self):
        super().__init__(
            "DDF00140",
            RuleTemplate.ERROR,
            "An organization type must be specified according to the extensible organization type (C188724) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
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
