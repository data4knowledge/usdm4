from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00166(RuleTemplate):
    """
    DDF00166: A study definition document type must be specified according to the extensible study definition document type (C215477) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: StudyDefinitionDocument
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00166",
            RuleTemplate.ERROR,
            "A study definition document type must be specified according to the extensible study definition document type (C215477) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "StudyDefinitionDocument", "type")
