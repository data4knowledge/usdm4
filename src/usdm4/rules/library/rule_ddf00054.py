from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00054(RuleTemplate):
    """
    DDF00054: Within an encounter there must be no duplicate contact modes.

    Applies to: Encounter
    Attributes: contactModes
    """

    def __init__(self):
        super().__init__(
            "DDF00054",
            RuleTemplate.ERROR,
            "Within an encounter there must be no duplicate contact modes.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Encounter"):
            values = []
            for sub in item.get("contactModes") or []:
                v = sub.get("code") if isinstance(sub, dict) else sub
                if v not in (None, ""):
                    values.append(v)
            if len(values) != len(set(values)):
                dupes = sorted(set(v for v in values if values.count(v) > 1))
                self._add_failure(
                    f"Duplicate contactModes entries: {dupes!r}",
                    "Encounter",
                    "contactModes",
                    data.path_by_id(item["id"]),
                )
        return self._result()
