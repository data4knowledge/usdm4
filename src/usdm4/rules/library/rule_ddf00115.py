from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00115(RuleTemplate):
    """
    DDF00115: Every study version must have a title of type "Official Study Title".

    Applies to: StudyVersion
    Attributes: titles
    """

    def __init__(self):
        super().__init__(
            "DDF00115",
            RuleTemplate.ERROR,
            'Every study version must have a title of type "Official Study Title".',
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00115: not yet implemented")
