from usdm3.rules.library.rule_template import RuleTemplate, JSONLocation


class Rule00015(RuleTemplate):
    """
    DDF00015: A study version's study phase must be specified according to the extensible Trial Phase Response (C66737) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).

    Applies to: StudyVersion
    Attributes: studyPhase
    """

    def __init__(self):
        super().__init__(
            "DDF00015",
            RuleTemplate.ERROR,
            "A study version's study phase must be specified according to the extensible Trial Phase Response (C66737) SDTM codelist (e.g. an entry with a code or decode used from the codelist should be consistent with the full entry in the codelist).",
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
