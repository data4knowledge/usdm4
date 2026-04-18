from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00026(RuleTemplate):
    """
    DDF00026: A scheduled activity instance must not point (via the "timeline" relationship) to the timeline in which it is specified.

    Applies to: ScheduledActivityInstance
    Attributes: timeline
    """

    def __init__(self):
        super().__init__(
            "DDF00026",
            RuleTemplate.ERROR,
            'A scheduled activity instance must not point (via the "timeline" relationship) to the timeline in which it is specified.',
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00026: not yet implemented")
