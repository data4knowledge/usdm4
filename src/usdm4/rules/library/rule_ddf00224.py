from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00224(RuleTemplate):
    """
    DDF00224: An observational study design's time perspective must be specified according to the extensible Observational Study Time Perspective (C127261) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: ObservationalStudyDesign
    Attributes: timePerspective
    """

    def __init__(self):
        super().__init__(
            "DDF00224",
            RuleTemplate.ERROR,
            "An observational study design's time perspective must be specified according to the extensible Observational Study Time Perspective (C127261) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "ObservationalStudyDesign", "timePerspective")
