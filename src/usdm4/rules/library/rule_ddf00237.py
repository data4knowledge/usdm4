from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00237(RuleTemplate):
    """
    DDF00237: The unit of a planned age is expected to be specified using terms from the Age Unit (C66781) SDTM codelist.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedAge
    """

    def __init__(self):
        super().__init__(
            "DDF00237",
            RuleTemplate.ERROR,
            "The unit of a planned age is expected to be specified using terms from the Age Unit (C66781) SDTM codelist.",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('StudyDesignPopulation', 'unit'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00237: not yet implemented")
