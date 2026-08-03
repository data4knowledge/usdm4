from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00183(RuleTemplate):
    """
    DDF00183: A reference identifier type must be specified according to the extensible reference identifier type (C215478) DDF codelist  (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: ReferenceIdentifier
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00183",
            RuleTemplate.ERROR,
            "A reference identifier type must be specified according to the extensible reference identifier type (C215478) DDF codelist  (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "ReferenceIdentifier", "type")
