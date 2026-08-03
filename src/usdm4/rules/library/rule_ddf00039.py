from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00039(RuleTemplate):
    """
    DDF00039: If the duration will vary, a quantity is not expected for the duration and vice versa.

    Applies to: Duration
    Attributes: quantity
    """

    def __init__(self):
        super().__init__(
            "DDF00039",
            RuleTemplate.WARNING,
            "If the duration will vary, a quantity is not expected for the duration and vice versa.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Duration"):
            a = item.get("durationWillVary") is True
            b = not bool(item.get("quantity"))
            if a != b:
                if a and not b:
                    msg = "durationWillVary is set but quantity is missing"
                else:
                    msg = "quantity is set but durationWillVary is missing"
                self._add_failure(
                    msg,
                    "Duration",
                    "durationWillVary, quantity",
                    data.path_by_id(item["id"]),
                )
        return self._result()
