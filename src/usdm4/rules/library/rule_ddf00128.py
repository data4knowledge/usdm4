from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00128(RuleTemplate):
    """
    DDF00128: A study intervention's type must be specified using the Intervention Type Response (C99078) SDTM codelist.

    Applies to: StudyIntervention
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00128",
            RuleTemplate.ERROR,
            "A study intervention's type must be specified using the Intervention Type Response (C99078) SDTM codelist.",
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
