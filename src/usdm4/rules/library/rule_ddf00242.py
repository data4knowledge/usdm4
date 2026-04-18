from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00242(RuleTemplate):
    """
    DDF00242: For each range, a unit must be specified either for both the minimum and the maximum value, or for neither of them.

    Applies to: Range
    Attributes: minValue, maxValue
    """

    def __init__(self):
        super().__init__(
            "DDF00242",
            RuleTemplate.ERROR,
            "For each range, a unit must be specified either for both the minimum and the maximum value, or for neither of them.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Range"):
            if not item.get("minValue"):
                self._add_failure(
                    "Required attribute 'minValue' is missing or empty",
                    "Range",
                    "minValue",
                    data.path_by_id(item["id"]),
                )
        return self._result()
