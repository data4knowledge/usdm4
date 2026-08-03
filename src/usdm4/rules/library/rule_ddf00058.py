from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00058(RuleTemplate):
    """
    DDF00058: Within an indication, if more indication codes are defined, they must be distinct.

    Applies to: Indication
    Attributes: codes
    """

    def __init__(self):
        super().__init__(
            "DDF00058",
            RuleTemplate.ERROR,
            "Within an indication, if more indication codes are defined, they must be distinct.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Indication"):
            values = []
            for sub in item.get("codes") or []:
                v = sub.get("code") if isinstance(sub, dict) else sub
                if v not in (None, ""):
                    values.append(v)
            if len(values) != len(set(values)):
                dupes = sorted(set(v for v in values if values.count(v) > 1))
                self._add_failure(
                    f"Duplicate codes entries: {dupes!r}",
                    "Indication",
                    "codes",
                    data.path_by_id(item["id"]),
                )
        return self._result()
