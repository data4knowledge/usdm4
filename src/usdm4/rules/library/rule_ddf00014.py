from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00014(RuleTemplate):
    """
    DDF00014: A biomedical concept category is expected to have at least a member or a child.

    Applies to: BiomedicalConceptCategory
    Attributes: members, children
    """

    def __init__(self):
        super().__init__(
            "DDF00014",
            RuleTemplate.WARNING,
            "A biomedical concept category is expected to have at least a member or a child.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00014: not yet implemented")
