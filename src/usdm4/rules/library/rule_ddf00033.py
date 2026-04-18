# MANUAL: do not regenerate
#
# At-least-one check on Duration: at least one of `text` (string) or
# `quantity` (embedded Quantity object) must be specified.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00033(RuleTemplate):
    """
    DDF00033: At least the text or the quantity must be specified for a duration.

    Applies to: Duration
    Attributes: text, quantity
    """

    def __init__(self):
        super().__init__(
            "DDF00033",
            RuleTemplate.ERROR,
            "At least the text or the quantity must be specified for a duration.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for duration in data.instances_by_klass("Duration"):
            text = duration.get("text")
            quantity = duration.get("quantity")
            has_text = isinstance(text, str) and text.strip() != ""
            has_quantity = quantity is not None and quantity != {}
            if not (has_text or has_quantity):
                self._add_failure(
                    "Duration has neither text nor quantity specified",
                    "Duration",
                    "text, quantity",
                    data.path_by_id(duration["id"]),
                )
        return self._result()
