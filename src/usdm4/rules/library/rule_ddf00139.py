from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00139(RuleTemplate):
    """
    DDF00139: An identified organization is not expected to have more than one identifier for the study.

    Applies to: StudyIdentifier
    Attributes: studyIdentifierScope
    """

    def __init__(self):
        super().__init__(
            "DDF00139",
            RuleTemplate.ERROR,
            "An identified organization is not expected to have more than one identifier for the study.",
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
