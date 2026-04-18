from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00178(RuleTemplate):
    """
    DDF00178: If a dose is specified then a corresponding frequency must also be specified.

    Applies to: Administration
    Attributes: dose
    """

    def __init__(self):
        super().__init__(
            "DDF00178",
            RuleTemplate.ERROR,
            "If a dose is specified then a corresponding frequency must also be specified.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Administration"):
            if bool(item.get("dose")) and not bool(item.get("frequency")):
                self._add_failure(
                    "dose is set but required frequency is missing",
                    "Administration",
                    "dose, frequency",
                    data.path_by_id(item["id"]),
                )
        return self._result()
