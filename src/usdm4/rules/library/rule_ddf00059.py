from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00059(RuleTemplate):
    """
    DDF00059: Within a study intervention, if more intervention codes are defined, they must be distinct.

    Applies to: StudyIntervention
    Attributes: codes
    """

    def __init__(self):
        super().__init__(
            "DDF00059",
            RuleTemplate.ERROR,
            "Within a study intervention, if more intervention codes are defined, they must be distinct.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("StudyIntervention"):
            values = []
            for sub in item.get("codes") or []:
                v = sub.get("code") if isinstance(sub, dict) else sub
                if v not in (None, ""):
                    values.append(v)
            if len(values) != len(set(values)):
                dupes = sorted(set(v for v in values if values.count(v) > 1))
                self._add_failure(
                    f"Duplicate codes entries: {dupes!r}",
                    "StudyIntervention",
                    "codes",
                    data.path_by_id(item["id"]),
                )
        return self._result()
