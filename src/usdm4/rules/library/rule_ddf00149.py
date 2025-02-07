from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class RuleDDF00149(RuleTemplate):
    """
    DDF00149: A study arm data origin type must be specified according to the extensible data origin type (C188727) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: StudyArm
    Attributes: dataOriginType
    """

    def __init__(self):
        super().__init__(
            "DDF00149",
            RuleTemplate.ERROR,
            "A study arm data origin type must be specified according to the extensible data origin type (C188727) DDF codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
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
