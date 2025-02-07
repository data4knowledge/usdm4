from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00103(RuleTemplate):
    """
    DDF00103: Within a document version, the specified section numbers for narrative content must be unique.

    Applies to: NarrativeContent
    Attributes: sectionNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00103",
            RuleTemplate.ERROR,
            "Within a document version, the specified section numbers for narrative content must be unique.",
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
