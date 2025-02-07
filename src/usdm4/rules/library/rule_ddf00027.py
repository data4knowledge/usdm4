from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00027(RuleTemplate):
    """
    DDF00027: To ensure consistent ordering, the same instance must not be referenced more than once as previous or next.

    Applies to: Activity, EligibilityCriterion, Encounter, NarrativeContent, StudyEpoch
    Attributes: previous, next
    """

    def __init__(self):
        super().__init__(
            "DDF00027",
            RuleTemplate.ERROR,
            "To ensure consistent ordering, the same instance must not be referenced more than once as previous or next.",
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
