from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00019(RuleTemplate):
    """
    DDF00019: A scheduled activity/decision instance must not refer to itself as its default condition.

    Applies to: ScheduledActivityInstance, ScheduledDecisionInstance
    Attributes: defaultCondition
    """

    def __init__(self):
        super().__init__(
            "DDF00019",
            RuleTemplate.ERROR,
            "A scheduled activity/decision instance must not refer to itself as its default condition.",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('ScheduledActivityInstance', 'instanceType'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00019: not yet implemented")
