from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00233(RuleTemplate):
    """
    DDF00233: A unit must be coded according to the extensible unit (C71620) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: Quantity
    Attributes: unit
    """

    def __init__(self):
        super().__init__(
            "DDF00233",
            RuleTemplate.ERROR,
            "A unit must be coded according to the extensible unit (C71620) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('Quantity', 'unit'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00233: not yet implemented")
