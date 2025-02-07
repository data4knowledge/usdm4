from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00100(RuleTemplate):
    """
    DDF00100: Within a study version, there must be no more than one title of each type.

    Applies to: StudyVersion
    Attributes: titles
    """

    def __init__(self):
        super().__init__(
            "DDF00100",
            RuleTemplate.ERROR,
            "Within a study version, there must be no more than one title of each type.",
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
