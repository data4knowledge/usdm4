from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00084(RuleTemplate):
    """
    DDF00084: Within a study design there must be exactly one objective with level 'Primary Objective'.

    Applies to: Objective
    Attributes: level
    """

    def __init__(self):
        super().__init__(
            "DDF00084",
            RuleTemplate.ERROR,
            "Within a study design there must be exactly one objective with level 'Primary Objective'.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00084: not yet implemented")
