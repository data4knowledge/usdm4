from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00208(RuleTemplate):
    """
    DDF00208: An administrable product sourcing must be specified using the extensible administrable product sourcing (C215483) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: AdministrableProduct
    Attributes: sourcing
    """

    def __init__(self):
        super().__init__(
            "DDF00208",
            RuleTemplate.ERROR,
            "An administrable product sourcing must be specified using the extensible administrable product sourcing (C215483) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "AdministrableProduct", "sourcing")
