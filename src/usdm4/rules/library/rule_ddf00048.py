from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00048(RuleTemplate):
    """
    DDF00048: A procedure must only reference a study intervention that is defined within the same study design as the activity within which the procedure is defined.

    Applies to: Procedure
    Attributes: studyIntervention
    """

    def __init__(self):
        super().__init__(
            "DDF00048",
            RuleTemplate.ERROR,
            "A procedure must only reference a study intervention that is defined within the same study design as the activity within which the procedure is defined.",
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
