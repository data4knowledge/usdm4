from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00200(RuleTemplate):
    """
    DDF00200: An organization type must be specified according to the extensible organization type (C188724) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: Organization
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00200",
            RuleTemplate.ERROR,
            "An organization type must be specified according to the extensible organization type (C188724) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "Organization", "type")
