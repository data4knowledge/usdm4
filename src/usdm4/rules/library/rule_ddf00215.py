from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00215(RuleTemplate):
    """
    DDF00215: An interventional study design's sub types must be specified according to the extensible Trial Type Response (C66739) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: InterventionalStudyDesign
    Attributes: subTypes
    """

    def __init__(self):
        super().__init__(
            "DDF00215",
            RuleTemplate.ERROR,
            "An interventional study design's sub types must be specified according to the extensible Trial Type Response (C66739) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('InterventionalStudyDesign', 'codeSystemVersion'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00215: not yet implemented")
