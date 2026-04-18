from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00017(RuleTemplate):
    """
    DDF00017: Within subject enrollment, the quantity must be a number or a percentage (i.e. the unit must be empty or %).

    Applies to: SubjectEnrollment
    Attributes: quantity
    """

    def __init__(self):
        super().__init__(
            "DDF00017",
            RuleTemplate.ERROR,
            "Within subject enrollment, the quantity must be a number or a percentage (i.e. the unit must be empty or %).",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00017: not yet implemented")
