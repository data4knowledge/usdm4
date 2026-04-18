# MANUAL: do not regenerate
#
# Strength.numerator is an embedded Quantity or Range. This rule covers the
# Quantity case: if the numerator has a `value`, it must also carry a
# non-empty `unit`. The Range case is handled by DDF00239.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00238(RuleTemplate):
    """
    DDF00238: If a strength numerator quantity is specified, it must have a unit.

    Applies to: Strength
    Attributes: numerator
    """

    def __init__(self):
        super().__init__(
            "DDF00238",
            RuleTemplate.ERROR,
            "If a strength numerator quantity is specified, it must have a unit.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for strength in data.instances_by_klass("Strength"):
            numerator = strength.get("numerator")
            if not isinstance(numerator, dict):
                continue
            # Quantity case: a `value` is present (not None). The Range case
            # has `minValue`/`maxValue` instead and is out of scope here.
            if numerator.get("value") is None:
                continue
            if not numerator.get("unit"):
                self._add_failure(
                    "Strength.numerator quantity has a value but no unit",
                    "Strength",
                    "numerator",
                    data.path_by_id(strength["id"]),
                )
        return self._result()
