from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00131(RuleTemplate):
    """
    DDF00131: Referenced items in the narrative content must be available elsewhere in the data model.

    Applies to: NarrativeContent
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00131",
            RuleTemplate.ERROR,
            "Referenced items in the narrative content must be available elsewhere in the data model.",
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
