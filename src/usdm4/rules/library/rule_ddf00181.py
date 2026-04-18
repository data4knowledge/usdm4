from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00181(RuleTemplate):
    """
    DDF00181: Date values associated to a study protocol document version must be unique regarding the combination of type and geographic scopes of the date.

    Applies to: StudyDefinitionDocumentVersion
    Attributes: dateValues
    """

    def __init__(self):
        super().__init__(
            "DDF00181",
            RuleTemplate.ERROR,
            "Date values associated to a study protocol document version must be unique regarding the combination of type and geographic scopes of the date.",
        )

    # TODO: implement. HIGH_UNIQUE_WITHIN_SCOPE without scope info — ambiguous (global vs per-parent vs intra-attribute). Review rule text.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00181: not yet implemented")
