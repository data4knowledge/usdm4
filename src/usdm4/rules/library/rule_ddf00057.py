from usdm3.rules.library.rule_template import RuleTemplate


class RuleDDF00057(RuleTemplate):
    """
    DDF00057: Within a study design, if more trial intent types are defined, they must be distinct.

    Applies to: StudyDesign
    Attributes: trialIntentTypes
    """

    def __init__(self):
        super().__init__(
            "DDF00057",
            RuleTemplate.ERROR,
            "Within a study design, if more trial intent types are defined, they must be distinct.",
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
