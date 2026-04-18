from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00152(RuleTemplate):
    """
    DDF00152: An activity must only reference timelines that are specified within the same study design.

    Applies to: Activity
    Attributes: timeline
    """

    def __init__(self):
        super().__init__(
            "DDF00152",
            RuleTemplate.ERROR,
            "An activity must only reference timelines that are specified within the same study design.",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('Activity', 'timelineId'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00152: not yet implemented")
