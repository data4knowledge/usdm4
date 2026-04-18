from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00110(RuleTemplate):
    """
    DDF00110: An eligibility criterion's category must be specified using the Category of Inclusion/Exclusion (C66797) SDTM codelist.

    Applies to: EligibilityCriterion
    Attributes: category
    """

    def __init__(self):
        super().__init__(
            "DDF00110",
            RuleTemplate.ERROR,
            "An eligibility criterion's category must be specified using the Category of Inclusion/Exclusion (C66797) SDTM codelist.",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('EligibilityCriterion', 'category'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00110: not yet implemented")
