# MANUAL: do not regenerate
#
# Delegated to DDF00082. Cardinality constraints (minItems/maxItems,
# single-value vs array typing) are enforced by the USDM JSON schema
# that DDF00082 runs against the input file. Running a separate check
# here would duplicate DDF00082's findings. No-op on purpose.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00126(RuleTemplate):
    """
    DDF00126: Cardinalities must be as defined in the USDM schema based on the API specification (i.e., required properties have at least one value and single-value properties are not lists).

    Applies to: All
    Attributes: All
    """

    def __init__(self):
        super().__init__(
            "DDF00126",
            RuleTemplate.ERROR,
            "Cardinalities must be as defined in the USDM schema based on the API specification (i.e., required properties have at least one value and single-value properties are not lists).",
        )

    def validate(self, config: dict) -> bool:
        # Covered by DDF00082 schema validation. See module docstring.
        return True
