from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00207(RuleTemplate):
    """
    DDF00207: A medical device identifier type must be specified according to the extensible medical device identifier type (C215484) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: MedicalDeviceIdentifier
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00207",
            RuleTemplate.ERROR,
            "A medical device identifier type must be specified according to the extensible medical device identifier type (C215484) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('MedicalDeviceIdentifier', 'type'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00207: not yet implemented")
