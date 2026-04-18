from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00020(RuleTemplate):
    """
    DDF00020: If the reason for a study amendment is 'Other' then this must be specified (attribute reasonOther must be completed), and vice versa.

    Applies to: StudyAmendmentReason
    Attributes: code, otherReason
    """

    def __init__(self):
        super().__init__(
            "DDF00020",
            RuleTemplate.ERROR,
            "If the reason for a study amendment is 'Other' then this must be specified (attribute reasonOther must be completed), and vice versa.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00020: not yet implemented")
