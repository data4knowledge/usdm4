from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00151(RuleTemplate):
    """
    DDF00151: If geographic scope type is global then there must be only one geographic scope specified.

    Applies to: GovernanceDate
    Attributes: geographicScopes
    """

    def __init__(self):
        super().__init__(
            "DDF00151",
            RuleTemplate.ERROR,
            "If geographic scope type is global then there must be only one geographic scope specified.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00151: not yet implemented")
