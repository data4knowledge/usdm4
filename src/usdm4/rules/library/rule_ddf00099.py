from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00099(RuleTemplate):
    """
    DDF00099: All epochs are expected to be referred to from a scheduled Activity Instance.

    Applies to: ScheduledActivityInstance
    Attributes: epoch
    """

    def __init__(self):
        super().__init__(
            "DDF00099",
            RuleTemplate.WARNING,
            "All epochs are expected to be referred to from a scheduled Activity Instance.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00099: not yet implemented")
