from usdm3.rules.library.rule_template import RuleTemplate


class RuleDDF00067(RuleTemplate):
    """
    DDF00067: A study cell must refer to at least one element.

    Applies to: StudyCell
    Attributes: elements
    """

    def __init__(self):
        super().__init__(
            "DDF00067",
            RuleTemplate.ERROR,
            "A study cell must refer to at least one element.",
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
