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

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "StudyDefinitionDocumentVersion", "status")
