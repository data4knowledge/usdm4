from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00009(RuleTemplate):
    """
    DDF00009: Each schedule timeline must contain at least one anchor (fixed time) - i.e., at least one scheduled activity instance that is referenced by a Fixed Reference timing.

    Applies to: Timing
    Attributes: type
    """

    def __init__(self):
        super().__init__(
            "DDF00009",
            RuleTemplate.ERROR,
            "Each schedule timeline must contain at least one anchor (fixed time) - i.e., at least one scheduled activity instance that is referenced by a Fixed Reference timing.",
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
