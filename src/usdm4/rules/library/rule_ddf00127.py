from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00127(RuleTemplate):
    """
    DDF00127: An encounter must only be scheduled at a timing that is defined within the same study design as the encounter.

    Applies to: Encounter
    Attributes: scheduledAt
    """

    def __init__(self):
        super().__init__(
            "DDF00127",
            RuleTemplate.ERROR,
            "An encounter must only be scheduled at a timing that is defined within the same study design as the encounter.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00127: not yet implemented")
