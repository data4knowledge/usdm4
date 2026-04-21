from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00052(RuleTemplate):
    """
    DDF00052: All standard code aliases referenced by an instance of the alias code class must be unique.

    Applies to: AliasCode
    Attributes: standardCodeAliases
    """

    def __init__(self):
        super().__init__(
            "DDF00052",
            RuleTemplate.ERROR,
            "All standard code aliases referenced by an instance of the alias code class must be unique.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("AliasCode"):
            values = []
            for sub in item.get("standardCodeAliases") or []:
                v = sub.get("code") if isinstance(sub, dict) else sub
                if v not in (None, ""):
                    values.append(v)
            if len(values) != len(set(values)):
                dupes = sorted(set(v for v in values if values.count(v) > 1))
                self._add_failure(
                    f"Duplicate standardCodeAliases entries: {dupes!r}",
                    "AliasCode",
                    "standardCodeAliases",
                    data.path_by_id(item["id"]),
                )
        return self._result()
