from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00095(RuleTemplate):
    """
    DDF00095: Within a study protocol document version, if a date of a specific type exists with a global geographic scope then no other dates are expected with the same type.

    Applies to: StudyProtocolDocumentVersion
    Attributes: dateValues
    """

    def __init__(self):
        super().__init__(
            "DDF00095",
            RuleTemplate.ERROR,
            "Within a study protocol document version, if a date of a specific type exists with a global geographic scope then no other dates are expected with the same type.",
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
