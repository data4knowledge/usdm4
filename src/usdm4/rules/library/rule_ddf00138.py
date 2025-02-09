from usdm3.rules.library.rule_template import RuleTemplate


class RuleDDF00138(RuleTemplate):
    """
    DDF00138: Every identifier must be unique within the scope of an identified organization.

    Applies to: StudyIdentifier
    Attributes: studyIdentifier
    """

    def __init__(self):
        super().__init__(
            "DDF00138",
            RuleTemplate.ERROR,
            "Every identifier must be unique within the scope of an identified organization.",
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
