from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00029(RuleTemplate):
    """
    DDF00029: An encounter must only reference encounters that are specified within the same study design.

    Applies to: Encounter
    Attributes: previous, next
    """

    def __init__(self):
        super().__init__(
            "DDF00029",
            RuleTemplate.ERROR,
            "An encounter must only reference encounters that are specified within the same study design.",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('Encounter', 'previousId'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00029: not yet implemented")
