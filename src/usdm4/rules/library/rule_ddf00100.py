from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00100(RuleTemplate):
    """
    DDF00100: Within a study version, there must be no more than one title of each type.

    Applies to: StudyVersion
    Attributes: titles
    """

    def __init__(self):
        super().__init__(
            "DDF00100",
            RuleTemplate.ERROR,
            "Within a study version, there must be no more than one title of each type.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("StudyVersion"):
            values = []
            for sub in item.get("titles") or []:
                v = sub.get("type.code") if isinstance(sub, dict) else sub
                if v not in (None, ""):
                    values.append(v)
            if len(values) != len(set(values)):
                dupes = sorted(set(v for v in values if values.count(v) > 1))
                self._add_failure(
                    f"Duplicate titles entries: {dupes!r}",
                    "StudyVersion",
                    "titles",
                    data.path_by_id(item["id"]),
                )
        return self._result()
