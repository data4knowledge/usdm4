from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00259(RuleTemplate):
    """
    DDF00259: A study role code must be specified according to the (C215480) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: StudyRole
    Attributes: code
    """

    def __init__(self):
        super().__init__(
            "DDF00259",
            RuleTemplate.ERROR,
            "A study role code must be specified according to the (C215480) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "StudyRole", "code")
