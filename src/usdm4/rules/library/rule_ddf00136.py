from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00136(RuleTemplate):
    """
    DDF00136: An encounter's contact modes must be specified according to the Mode of Subject Contact (C171445) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: Encounter
    Attributes: contactModes
    """

    def __init__(self):
        super().__init__(
            "DDF00136",
            RuleTemplate.ERROR,
            "An encounter's contact modes must be specified according to the Mode of Subject Contact (C171445) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('Encounter', 'codeSystemVersion'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00136: not yet implemented")
