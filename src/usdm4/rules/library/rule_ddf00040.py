from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00040(RuleTemplate):
    """
    DDF00040: Each study element must be referenced by at least one study cell.

    Applies to: StudyCell
    Attributes: elements
    """

    def __init__(self):
        super().__init__(
            "DDF00040",
            RuleTemplate.ERROR,
            "Each study element must be referenced by at least one study cell.",
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
