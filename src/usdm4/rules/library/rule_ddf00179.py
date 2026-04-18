from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00179(RuleTemplate):
    """
    DDF00179: An administrable dose form must be specified according to the extensible Pharmaceutical Dosage Form (C66726) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: AdministrableProduct
    Attributes: administrableDoseForm
    """

    def __init__(self):
        super().__init__(
            "DDF00179",
            RuleTemplate.ERROR,
            "An administrable dose form must be specified according to the extensible Pharmaceutical Dosage Form (C66726) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "AdministrableProduct", "administrableDoseForm")
