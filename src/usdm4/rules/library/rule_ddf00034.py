from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00034(RuleTemplate):
    """
    DDF00034: If duration will vary (attribute durationWillVary is True) then a reason (attribute reasonDurationWillVary) must be given and vice versa.

    Applies to: Duration
    Attributes: durationWillVary, reasonDurationWillVary
    """

    def __init__(self):
        super().__init__(
            "DDF00034",
            RuleTemplate.ERROR,
            "If duration will vary (attribute durationWillVary is True) then a reason (attribute reasonDurationWillVary) must be given and vice versa.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Duration"):
            a = (item.get("durationWillVary") is True)
            b = bool(item.get("reasonDurationWillVary"))
            if a != b:
                if a and not b:
                    msg = "durationWillVary is set but reasonDurationWillVary is missing"
                else:
                    msg = "reasonDurationWillVary is set but durationWillVary is missing"
                self._add_failure(
                    msg,
                    "Duration",
                    "durationWillVary, reasonDurationWillVary",
                    data.path_by_id(item["id"]),
                )
        return self._result()
