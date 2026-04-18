from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00210(RuleTemplate):
    """
    DDF00210: An administrable product's product designation must be specified using the product designation (C207418) DDF codelist.

    Applies to: StudyIntervention
    Attributes: productDesignation
    """

    def __init__(self):
        super().__init__(
            "DDF00210",
            RuleTemplate.ERROR,
            "An administrable product's product designation must be specified using the product designation (C207418) DDF codelist.",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('StudyIntervention', 'productDesignation'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00210: not yet implemented")
