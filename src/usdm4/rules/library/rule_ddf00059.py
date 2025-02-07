from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00059(RuleTemplate):
    """
    DDF00059: Within a study intervention, if more intervention codes are defined, they must be distinct.

    Applies to: StudyIntervention
    Attributes: codes
    """

    def __init__(self):
        super().__init__(
            "DDF00059",
            RuleTemplate.ERROR,
            "Within a study intervention, if more intervention codes are defined, they must be distinct.",
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
