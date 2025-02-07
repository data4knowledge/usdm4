from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00035(RuleTemplate):
    """
    DDF00035: Within a code system and corresponding version, a one-to-one relationship between code and decode is expected.

    Applies to: Code
    Attributes: code, decode
    """

    def __init__(self):
        super().__init__(
            "DDF00035",
            RuleTemplate.ERROR,
            "Within a code system and corresponding version, a one-to-one relationship between code and decode is expected.",
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
