from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00184(RuleTemplate):
    """
    DDF00184: A substance must not references itself as a reference substance.

    Applies to: Substance
    Attributes: referenceSubstance
    """

    def __init__(self):
        super().__init__(
            "DDF00184",
            RuleTemplate.ERROR,
            "A substance must not references itself as a reference substance.",
        )

    # TODO: implement. STUB: rule not present in CORE catalogue
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00184: not yet implemented")
