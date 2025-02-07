from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00108(RuleTemplate):
    """
    DDF00108: There must be at least one exit defined for each timeline (i.e., at least one instance of StudyTimelineExit linked via the 'exits' relationship).

    Applies to: ScheduleTimeline
    Attributes: exits
    """

    def __init__(self):
        super().__init__(
            "DDF00108",
            RuleTemplate.ERROR,
            "There must be at least one exit defined for each timeline (i.e., at least one instance of StudyTimelineExit linked via the 'exits' relationship).",
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
