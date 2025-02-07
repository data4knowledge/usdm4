from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00080(RuleTemplate):
    """
    DDF00080: All scheduled activity instances are expected to refer to an epoch.

    Applies to: ScheduledActivityInstance
    Attributes: epoch
    """

    def __init__(self):
        super().__init__(
            "DDF00080",
            RuleTemplate.ERROR,
            "All scheduled activity instances are expected to refer to an epoch.",
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
