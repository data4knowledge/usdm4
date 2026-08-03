from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00090(RuleTemplate):
    """
    DDF00090: The same Biomedical Concept Category must not be referenced more than once from the same activity.

    Applies to: Activity
    Attributes: bcCategories
    """

    def __init__(self):
        super().__init__(
            "DDF00090",
            RuleTemplate.ERROR,
            "The same Biomedical Concept Category must not be referenced more than once from the same activity.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Activity"):
            values = []
            for sub in item.get("bcCategories") or []:
                v = sub.get("id") if isinstance(sub, dict) else sub
                if v not in (None, ""):
                    values.append(v)
            if len(values) != len(set(values)):
                dupes = sorted(set(v for v in values if values.count(v) > 1))
                self._add_failure(
                    f"Duplicate bcCategories entries: {dupes!r}",
                    "Activity",
                    "bcCategories",
                    data.path_by_id(item["id"]),
                )
        return self._result()
