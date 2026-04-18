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

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('ObservationalStudyDesign', 'studyType'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00230: not yet implemented")
