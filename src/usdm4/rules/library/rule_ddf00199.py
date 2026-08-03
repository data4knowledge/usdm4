from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00199(RuleTemplate):
    """
    DDF00199: An study impact type must be specified according to the extensible study amendment impact type (C215481) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: StudyAmendmentImpact
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00199",
            RuleTemplate.ERROR,
            "An study impact type must be specified according to the extensible study amendment impact type (C215481) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "StudyAmendmentImpact", "type")
