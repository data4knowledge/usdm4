from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00152(RuleTemplate):
    """
    DDF00152: An activity must only reference timelines that are specified within the same study design.

    Applies to: Activity
    Attributes: timeline
    """

    def __init__(self):
        super().__init__(
            "DDF00152",
            RuleTemplate.ERROR,
            "An activity must only reference timelines that are specified within the same study design.",
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
