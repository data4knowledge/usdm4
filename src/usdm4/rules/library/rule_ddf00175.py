from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00175(RuleTemplate):
    """
    DDF00175: An administration's frequency must be specified according to the extensible Frequency (C71113) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: Administration
    Attributes: frequency
    """

    def __init__(self):
        super().__init__(
            "DDF00175",
            RuleTemplate.ERROR,
            "An administration's frequency must be specified according to the extensible Frequency (C71113) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "Administration", "frequency")
