from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00092(RuleTemplate):
    """
    DDF00092: Date values associated to a study protocol document version must be unique regarding the combination of type and geographic scopes of the date.

    Applies to: StudyProtocolDocumentVersion
    Attributes: dateValues
    """

    def __init__(self):
        super().__init__(
            "DDF00092",
            RuleTemplate.ERROR,
            "Date values associated to a study protocol document version must be unique regarding the combination of type and geographic scopes of the date.",
        )

    def validate(self, config: dict) -> bool:
        """
        Validate the rule against the provided data

        Args:
            config (dict): Standard configuration structure contain the data, CT etc

        Returns:
            bool: True if validation passes
        """
        raise NotImplementedError("rule is not implemented")
