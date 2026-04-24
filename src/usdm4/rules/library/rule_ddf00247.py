# MANUAL: do not regenerate
#
# Syntax template text across six classes must be valid USDM-XHTML.
# Delegates to the shared `xhtml_validation` module that wraps lxml +
# the bundled XML Schema (see rule_ddf00187.py for the same rationale).
from usdm4.rules.rule_template import RuleTemplate
from usdm4.rules.xhtml_validation import get_validator


SCOPE_CLASSES = [
    "EligibilityCriterionItem",
    "Characteristic",
    "Condition",
    "Objective",
    "Endpoint",
    "IntercurrentEvent",
]


class RuleDDF00247(RuleTemplate):
    """
    DDF00247: Syntax template text is expected to be HTML formatted.

    Applies to: EligibilityCriterionItem, Characteristic, Condition, Objective, Endpoint, IntercurrentEvent
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00247",
            RuleTemplate.WARNING,
            "Syntax template text is expected to be HTML formatted.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        validator = get_validator()
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                text = instance.get("text")
                if not isinstance(text, str) or text.strip() == "":
                    continue
                errors = validator.validate(text)
                if not errors:
                    continue
                summary = "; ".join(
                    f"line {e.line}: {e.message[:160]}" if e.line else e.message[:160]
                    for e in errors[:3]
                )
                if len(errors) > 3:
                    summary += f"; ... and {len(errors) - 3} more"
                self._add_failure(
                    f"{klass}.text is not valid USDM-XHTML — {summary}",
                    klass,
                    "text",
                    data.path_by_id(instance["id"]),
                )
        return self._result()
