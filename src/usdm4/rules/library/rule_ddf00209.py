from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00209(RuleTemplate):
    """
    DDF00209: A medical device sourcing must be specified using the extensible medical device sourcing (C215482) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: MedicalDevice
    Attributes: sourcing
    """

    def __init__(self):
        super().__init__(
            "DDF00209",
            RuleTemplate.ERROR,
            "A medical device sourcing must be specified using the extensible medical device sourcing (C215482) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "MedicalDevice", "sourcing")
