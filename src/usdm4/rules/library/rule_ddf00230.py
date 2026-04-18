from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00230(RuleTemplate):
    """
    DDF00230: A study design's study type must be specified using the Study Type Response (C99077) SDTM codelist.

    Applies to: ObservationalStudyDesign, InterventionalStudyDesign
    Attributes: studyType
    """

    def __init__(self):
        super().__init__(
            "DDF00230",
            RuleTemplate.ERROR,
            "A study design's study type must be specified using the Study Type Response (C99077) SDTM codelist.",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "ObservationalStudyDesign", "studyType")
