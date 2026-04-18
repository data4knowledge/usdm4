from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00229(RuleTemplate):
    """
    DDF00229: A study design's study phase must be specified according to the extensible Trial Phase Response (C66737) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: ObservationalStudyDesign, InterventionalStudyDesign
    Attributes: studyPhase
    """

    def __init__(self):
        super().__init__(
            "DDF00229",
            RuleTemplate.ERROR,
            "A study design's study phase must be specified according to the extensible Trial Phase Response (C66737) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "ObservationalStudyDesign", "studyPhase")
