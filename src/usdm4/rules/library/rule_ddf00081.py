from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00081(RuleTemplate):
    """
    DDF00081: Class relationships must conform with the USDM schema based on the API specification.

    Applies to: All
    Attributes: All
    """

    def __init__(self):
        super().__init__(
            "DDF00081",
            RuleTemplate.ERROR,
            "Class relationships must conform with the USDM schema based on the API specification.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00081: not yet implemented")
