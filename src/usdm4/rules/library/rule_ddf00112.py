from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00112(RuleTemplate):
    """
    DDF00112: A study intervention's role must be specified using the study intervention role (C207417) DDF codelist.

    Applies to: StudyIntervention
    Attributes: role
    """

    def __init__(self):
        super().__init__(
            "DDF00112",
            RuleTemplate.ERROR,
            "A study intervention's role must be specified using the study intervention role (C207417) DDF codelist.",
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
