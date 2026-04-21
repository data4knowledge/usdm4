from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00217(RuleTemplate):
    """
    DDF00217: A study design's blinding schema must be specified according to the extensible Trial Blinding Schema Response (C66735) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: InterventionalStudyDesign
    Attributes: blindingSchema
    """

    def __init__(self):
        super().__init__(
            "DDF00217",
            RuleTemplate.ERROR,
            "A study design's blinding schema must be specified according to the extensible Trial Blinding Schema Response (C66735) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "InterventionalStudyDesign", "blindingSchema")
