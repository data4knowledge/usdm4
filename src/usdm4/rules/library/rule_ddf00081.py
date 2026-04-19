# MANUAL: do not regenerate
#
# Delegated to DDF00082. The full USDM API specification is enforced
# there via jsonschema against src/usdm4/rules/library/schema/
# usdm_v4-0-0.json, which covers class relationships as part of the
# schema. Running a separate check here would duplicate DDF00082's
# findings with different framing. No-op on purpose.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00081(RuleTemplate):
    """
    DDF00081: Class relationships must conform with the USDM schema based on the API specification.

    Applies to: All
    Attributes: All
    """

    def __init__(self):
        super().__init__(
            "DDF00081",
            RuleTemplate.ERROR,
            "Class relationships must conform with the USDM schema based on the API specification.",
        )

    def validate(self, config: dict) -> bool:
        # Covered by DDF00082 schema validation. See module docstring.
        return True
