from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00214(RuleTemplate):
    """
    DDF00214: An interventional study design's intent types must be specified according to the extensible Trial Intent Type Response (C66736) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: InterventionalStudyDesign
    Attributes: intentTypes
    """

    def __init__(self):
        super().__init__(
            "DDF00214",
            RuleTemplate.ERROR,
            "An interventional study design's intent types must be specified according to the extensible Trial Intent Type Response (C66736) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "InterventionalStudyDesign", "intentTypes")
