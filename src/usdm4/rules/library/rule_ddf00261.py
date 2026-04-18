from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00261(RuleTemplate):
    """
    DDF00261: If a geographic scope type is global then no code is expected to specify the specific area within scope while if it is not global then a code is expected to specify the specific area within scope.

    Applies to: GeographicScope
    Attributes: code
    """

    def __init__(self):
        super().__init__(
            "DDF00261",
            RuleTemplate.WARNING,
            "If a geographic scope type is global then no code is expected to specify the specific area within scope while if it is not global then a code is expected to specify the specific area within scope.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("GeographicScope"):
            a = (isinstance(item.get("type"), dict) and item["type"].get("code") == "C68846")
            b = (not bool(item.get("code")))
            if a != b:
                if a and not b:
                    msg = "type is set but code is missing"
                else:
                    msg = "code is set but type is missing"
                self._add_failure(
                    msg,
                    "GeographicScope",
                    "type, code",
                    data.path_by_id(item["id"]),
                )
        return self._result()
