from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00156(RuleTemplate):
    """
    DDF00156: Within an encounter, if more environmental settings are defined, they must be distinct.

    Applies to: Encounter
    Attributes: environmentalSettings
    """

    def __init__(self):
        super().__init__(
            "DDF00156",
            RuleTemplate.ERROR,
            "Within an encounter, if more environmental settings are defined, they must be distinct.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Encounter"):
            values = []
            for sub in item.get("environmentalSettings") or []:
                v = sub.get("code") if isinstance(sub, dict) else sub
                if v not in (None, ""):
                    values.append(v)
            if len(values) != len(set(values)):
                dupes = sorted(set(v for v in values if values.count(v) > 1))
                self._add_failure(
                    f"Duplicate environmentalSettings entries: {dupes!r}",
                    "Encounter",
                    "environmentalSettings",
                    data.path_by_id(item["id"]),
                )
        return self._result()
