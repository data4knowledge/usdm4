from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00146(RuleTemplate):
    """
    DDF00146: A study title type must be specified using the study title type (C207419) DDF codelist.

    Applies to: StudyTitle
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00146",
            RuleTemplate.ERROR,
            "A study title type must be specified using the study title type (C207419) DDF codelist.",
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
