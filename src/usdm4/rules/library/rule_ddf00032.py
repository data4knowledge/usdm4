from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00032(RuleTemplate):
    """
    DDF00032: Within a study version, if more than 1 business therapeutic area is defined then they must be distinct.

    Applies to: StudyVersion
    Attributes: businessTherapeuticAreas
    """

    def __init__(self):
        super().__init__(
            "DDF00032",
            RuleTemplate.ERROR,
            "Within a study version, if more than 1 business therapeutic area is defined then they must be distinct.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("StudyVersion"):
            values = []
            for sub in item.get("businessTherapeuticAreas") or []:
                v = sub.get("code") if isinstance(sub, dict) else sub
                if v not in (None, ""):
                    values.append(v)
            if len(values) != len(set(values)):
                dupes = sorted(set(v for v in values if values.count(v) > 1))
                self._add_failure(
                    f"Duplicate businessTherapeuticAreas entries: {dupes!r}",
                    "StudyVersion",
                    "businessTherapeuticAreas",
                    data.path_by_id(item["id"]),
                )
        return self._result()
