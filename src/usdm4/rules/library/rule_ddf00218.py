from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00218(RuleTemplate):
    """
    DDF00218: A study design's characteristics must be specified according to the extensible study design characteristics (C207416) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: characteristics
    """

    def __init__(self):
        super().__init__(
            "DDF00218",
            RuleTemplate.ERROR,
            "A study design's characteristics must be specified according to the extensible study design characteristics (C207416) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('InterventionalStudyDesign', 'codeSystemVersion'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00218: not yet implemented")
