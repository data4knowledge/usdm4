from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00042(RuleTemplate):
    """
    DDF00042: The range specified for a planned age is not expected to be approximate.

    Applies to: Range
    Attributes: isApproximate
    """

    def __init__(self):
        super().__init__(
            "DDF00042",
            RuleTemplate.WARNING,
            "The range specified for a planned age is not expected to be approximate.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00042: not yet implemented")
