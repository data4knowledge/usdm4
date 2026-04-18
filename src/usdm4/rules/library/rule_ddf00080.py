from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00080(RuleTemplate):
    """
    DDF00080: All scheduled activity instances are expected to refer to an epoch.

    Applies to: ScheduledActivityInstance
    Attributes: epoch
    """

    def __init__(self):
        super().__init__(
            "DDF00080",
            RuleTemplate.WARNING,
            "All scheduled activity instances are expected to refer to an epoch.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00080: not yet implemented")
