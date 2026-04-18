from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00013(RuleTemplate):
    """
    DDF00013: If a biomedical concept property is required then it must also be enabled, while if it is not enabled then it must not be required.

    Applies to: BiomedicalConceptProperty
    Attributes: isRequired, isEnabled
    """

    def __init__(self):
        super().__init__(
            "DDF00013",
            RuleTemplate.ERROR,
            "If a biomedical concept property is required then it must also be enabled, while if it is not enabled then it must not be required.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00013: not yet implemented")
