from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00177(RuleTemplate):
    """
    DDF00177: If an administration's dose is specified then a corresponding route is expected and vice versa.

    Applies to: Administration
    Attributes: dose, route
    """

    def __init__(self):
        super().__init__(
            "DDF00177",
            RuleTemplate.WARNING,
            "If an administration's dose is specified then a corresponding route is expected and vice versa.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Administration"):
            a = bool(item.get("dose"))
            b = bool(item.get("route"))
            if a != b:
                if a and not b:
                    msg = "dose is set but route is missing"
                else:
                    msg = "route is set but dose is missing"
                self._add_failure(
                    msg,
                    "Administration",
                    "dose, route",
                    data.path_by_id(item["id"]),
                )
        return self._result()
