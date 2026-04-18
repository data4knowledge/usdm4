from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00024(RuleTemplate):
    """
    DDF00024: An epoch must only reference epochs that are specified within the same study design.

    Applies to: StudyEpoch
    Attributes: previous, next
    """

    def __init__(self):
        super().__init__(
            "DDF00024",
            RuleTemplate.ERROR,
            "An epoch must only reference epochs that are specified within the same study design.",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('StudyEpoch', 'previousId'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00024: not yet implemented")
