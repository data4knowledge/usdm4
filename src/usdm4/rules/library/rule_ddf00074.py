from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00074(RuleTemplate):
    """
    DDF00074: If the intervention model indicates a single group design then only one intervention is expected. In all other cases more interventions are expected.

    Applies to: StudyDesign
    Attributes: studyInterventions
    """

    def __init__(self):
        super().__init__(
            "DDF00074",
            RuleTemplate.ERROR,
            "If the intervention model indicates a single group design then only one intervention is expected. In all other cases more interventions are expected.",
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
