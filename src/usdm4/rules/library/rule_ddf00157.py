from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00157(RuleTemplate):
    """
    DDF00157: An encounter's environmental settings must be specified according to the extensible Environmental Setting (C127262) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: Encounter
    Attributes: environmentalSettings
    """

    def __init__(self):
        super().__init__(
            "DDF00157",
            RuleTemplate.ERROR,
            "An encounter's environmental settings must be specified according to the extensible Environmental Setting (C127262) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "Encounter", "environmentalSettings")
