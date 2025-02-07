from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00012(RuleTemplate):
    """
    DDF00012: Within a study design, there must be exactly one scheduled timeline which identifies as the main Timeline.

    Applies to: ScheduleTimeline
    Attributes: mainTimeline
    """

    def __init__(self):
        super().__init__(
            "DDF00012",
            RuleTemplate.ERROR,
            "Within a study design, there must be exactly one scheduled timeline which identifies as the main Timeline.",
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
