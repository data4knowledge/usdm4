# MANUAL: do not regenerate
#
# Range case of Strength.numerator. When minValue / maxValue are present
# (each an embedded Quantity with its own `value`), each must carry a
# non-empty `unit`.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00239(RuleTemplate):
    """
    DDF00239: If a strength numerator range is specified, both the minValue and maxValue must have a unit.

    Applies to: Strength
    Attributes: numerator
    """

    def __init__(self):
        super().__init__(
            "DDF00239",
            RuleTemplate.ERROR,
            "If a strength numerator range is specified, both the minValue and maxValue must have a unit.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for strength in data.instances_by_klass("Strength"):
            numerator = strength.get("numerator")
            if not isinstance(numerator, dict):
                continue
            min_value = numerator.get("minValue")
            max_value = numerator.get("maxValue")
            if not (isinstance(min_value, dict) or isinstance(max_value, dict)):
                continue  # not a Range
            for endpoint_name, endpoint in (
                ("minValue", min_value),
                ("maxValue", max_value),
            ):
                if not isinstance(endpoint, dict):
                    continue
                if endpoint.get("value") is not None and not endpoint.get("unit"):
                    self._add_failure(
                        f"Strength.numerator.{endpoint_name} has a value but no unit",
                        "Strength",
                        "numerator",
                        data.path_by_id(strength["id"]),
                    )
        return self._result()
