from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00143(RuleTemplate):
    """
    DDF00143: A study amendment reason must be coded using the study amendment reason (C207415) DDF codelist.

    Applies to: StudyAmendmentReason
    Attributes: code
    """

    def __init__(self):
        super().__init__(
            "DDF00143",
            RuleTemplate.ERROR,
            "A study amendment reason must be coded using the study amendment reason (C207415) DDF codelist.",
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
