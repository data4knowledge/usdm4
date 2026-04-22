# MANUAL: do not regenerate
#
# Range.minValue and Range.maxValue are each an embedded Quantity
# { value, unit }. Per CORE:
#   $EqUnit = (minValue.unit.standardCode.code == maxValue.unit.standardCode.code)
#              OR (both units missing/null)
#   fail if $EqUnit AND (maxValue.value <= minValue.value)
# When units differ, the comparison is skipped — this rule doesn't
# handle unit conversion.
from usdm4.rules.rule_template import RuleTemplate


def _unit_code(endpoint):
    """Return the Code.code string identifying the unit, or None if the unit is absent."""
    if not isinstance(endpoint, dict):
        return None
    unit = endpoint.get("unit")
    if not isinstance(unit, dict):
        return None
    standard = unit.get("standardCode")
    if isinstance(standard, dict):
        return standard.get("code")
    return unit.get("code")


class RuleDDF00241(RuleTemplate):
    """
    DDF00241: If the unit is the same (or missing) for both the minimum and maximum value, then the minimum value must be less than the maximum value.

    Applies to: Range
    Attributes: minValue, maxValue
    """

    def __init__(self):
        super().__init__(
            "DDF00241",
            RuleTemplate.ERROR,
            "If the unit is the same (or missing) for both the minimum and maximum value, then the minimum value must be less than the maximum value.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for range_inst in data.instances_by_klass("Range"):
            min_endpoint = range_inst.get("minValue")
            max_endpoint = range_inst.get("maxValue")
            if not (isinstance(min_endpoint, dict) and isinstance(max_endpoint, dict)):
                continue
            min_val = min_endpoint.get("value")
            max_val = max_endpoint.get("value")
            if not isinstance(min_val, (int, float)) or not isinstance(
                max_val, (int, float)
            ):
                continue
            min_unit_code = _unit_code(min_endpoint)
            max_unit_code = _unit_code(max_endpoint)
            same_unit = min_unit_code == max_unit_code
            if not same_unit:
                continue
            if max_val <= min_val:
                self._add_failure(
                    f"Range.maxValue ({max_val}) <= minValue ({min_val}) with matching/absent units",
                    "Range",
                    "minValue, maxValue",
                    data.path_by_id(range_inst["id"]),
                )
        return self._result()
