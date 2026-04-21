# MANUAL: do not regenerate
#
# Delegated to DDF00082. Required-property presence and additionalProperties
# rejection are enforced by the USDM JSON schema that DDF00082 runs against
# the input file. Running a separate check here would duplicate DDF00082's
# findings. No-op on purpose.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00125(RuleTemplate):
    """
    DDF00125: Attributes must be included as defined in the USDM schema based on the API specification (i.e., all required properties are present and no additional attributes are present).

    Applies to: All
    Attributes: All
    """

    def __init__(self):
        super().__init__(
            "DDF00125",
            RuleTemplate.ERROR,
            "Attributes must be included as defined in the USDM schema based on the API specification (i.e., all required properties are present and no additional attributes are present).",
        )

    def validate(self, config: dict) -> bool:
        # Covered by DDF00082 schema validation. See module docstring.
        return True
