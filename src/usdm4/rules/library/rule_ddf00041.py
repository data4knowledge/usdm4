from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00041(RuleTemplate):
    """
    DDF00041: Within a study design, there must be at least one endpoint with level primary.

    Applies to: Endpoint
    Attributes: level
    """

    def __init__(self):
        super().__init__(
            "DDF00041",
            RuleTemplate.ERROR,
            "Within a study design, there must be at least one endpoint with level primary.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Endpoint"):
            if not item.get("level"):
                self._add_failure(
                    "Required attribute 'level' is missing or empty",
                    "Endpoint",
                    "level",
                    data.path_by_id(item["id"]),
                )
        return self._result()
