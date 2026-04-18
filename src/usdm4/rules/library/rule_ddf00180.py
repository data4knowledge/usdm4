from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00180(RuleTemplate):
    """
    DDF00180: An administrable product property type must be specified according to the extensible administrable property type (C215479) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: AdministrableProductProperty
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00180",
            RuleTemplate.ERROR,
            "An administrable product property type must be specified according to the extensible administrable property type (C215479) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('AdministrableProductProperty', 'type'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00180: not yet implemented")
