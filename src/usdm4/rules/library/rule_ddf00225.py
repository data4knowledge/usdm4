from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00225(RuleTemplate):
    """
    DDF00225: An observational study design's sampling method must be specified according to the extensible Observational Study Sampling Method (C127260) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: ObservationalStudyDesign
    Attributes: samplingMethod
    """

    def __init__(self):
        super().__init__(
            "DDF00225",
            RuleTemplate.ERROR,
            "An observational study design's sampling method must be specified according to the extensible Observational Study Sampling Method (C127260) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "ObservationalStudyDesign", "samplingMethod")
