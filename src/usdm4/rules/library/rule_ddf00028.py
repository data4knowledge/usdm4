from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00028(RuleTemplate):
    """
    DDF00028: An activity must only reference activities that are specified within the same study design.

    Applies to: Activity
    Attributes: previous, next
    """

    def __init__(self):
        super().__init__(
            "DDF00028",
            RuleTemplate.ERROR,
            "An activity must only reference activities that are specified within the same study design.",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('Activity', 'previousId'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00028: not yet implemented")
