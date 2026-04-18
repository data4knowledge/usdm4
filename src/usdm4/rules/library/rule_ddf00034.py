from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00034(RuleTemplate):
    """
    DDF00034: If duration will vary (attribute durationWillVary is True) then a reason (attribute reasonDurationWillVary) must be given and vice versa.

    Applies to: Duration
    Attributes: durationWillVary, reasonDurationWillVary
    """

    def __init__(self):
        super().__init__(
            "DDF00034",
            RuleTemplate.ERROR,
            "If duration will vary (attribute durationWillVary is True) then a reason (attribute reasonDurationWillVary) must be given and vice versa.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00034: not yet implemented")
