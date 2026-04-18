from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00226(RuleTemplate):
    """
    DDF00226: A observational study design's sub types must be specified according to the extensible observational study design type (C215486) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: ObservationalStudyDesign
    Attributes: subTypes
    """

    def __init__(self):
        super().__init__(
            "DDF00226",
            RuleTemplate.ERROR,
            "A observational study design's sub types must be specified according to the extensible observational study design type (C215486) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "ObservationalStudyDesign", "subTypes")
