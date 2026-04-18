from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00187(RuleTemplate):
    """
    DDF00187: Narrative content item text is expected to be HTML formatted.

    Applies to: NarrativeContentItem
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00187",
            RuleTemplate.WARNING,
            "Narrative content item text is expected to be HTML formatted.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00187: not yet implemented")
