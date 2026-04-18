from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00169(RuleTemplate):
    """
    DDF00169: A study definition document version's status must be specified using the status Value Set Terminology (C188723) DDF codelist.

    Applies to: StudyDefinitionDocumentVersion
    Attributes: status
    """

    def __init__(self):
        super().__init__(
            "DDF00169",
            RuleTemplate.ERROR,
            "A study definition document version's status must be specified using the status Value Set Terminology (C188723) DDF codelist.",
        )

    # TODO: implement. HIGH_CT_MEMBER with no CT codelist registered for ('StudyDefinitionDocumentVersion', 'status'). Update ct_config.yaml or revise the rule's class/attribute before implementing.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00169: not yet implemented")
