from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00038(RuleTemplate):
    """
    DDF00038: A scheduled decision instance must refer to a default condition.

    Applies to: ScheduledDecisionInstance
    Attributes: defaultCondition
    """

    def __init__(self):
        super().__init__(
            "DDF00038",
            RuleTemplate.ERROR,
            "A scheduled decision instance must refer to a default condition.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00038: not yet implemented")
