from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00247(RuleTemplate):
    """
    DDF00247: Syntax template text is expected to be HTML formatted.

    Applies to: EligibilityCriterionItem, Characteristic, Condition, Objective, Endpoint, IntercurrentEvent
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00247",
            RuleTemplate.WARNING,
            "Syntax template text is expected to be HTML formatted.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00247: not yet implemented")
