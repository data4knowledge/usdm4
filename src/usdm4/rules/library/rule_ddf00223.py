from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00223(RuleTemplate):
    """
    DDF00223: A study design's observational model must be specified according to the extensible Observational Study Model (C127259) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: ObservationalStudyDesign
    Attributes: model
    """

    def __init__(self):
        super().__init__(
            "DDF00223",
            RuleTemplate.ERROR,
            "A study design's observational model must be specified according to the extensible Observational Study Model (C127259) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "ObservationalStudyDesign", "model")
