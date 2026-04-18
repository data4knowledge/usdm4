from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00046(RuleTemplate):
    """
    DDF00046: A timing must only be specified as being relative to/from a scheduled activity/decision instance that is defined within the same timeline as the timing.

    Applies to: Timing
    Attributes: relativeFromScheduledInstance, relativeToScheduledInstance
    """

    def __init__(self):
        super().__init__(
            "DDF00046",
            RuleTemplate.ERROR,
            "A timing must only be specified as being relative to/from a scheduled activity/decision instance that is defined within the same timeline as the timing.",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('ScheduledDecisionInstance', 'parent_id'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00046: not yet implemented")
