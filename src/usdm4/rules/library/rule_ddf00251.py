from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00251(RuleTemplate):
    """
    DDF00251: A study cohort must only reference indications that are  defined within the same study design.

    Applies to: StudyCohort
    Attributes: indications
    """

    def __init__(self):
        super().__init__(
            "DDF00251",
            RuleTemplate.ERROR,
            "A study cohort must only reference indications that are  defined within the same study design.",
        )

    # GENERATED — predicate inferred from rule text, please review.
    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import any_ids_unresolved
        data = config["data"]
        for item in data.instances_by_klass("StudyCohort"):
            raw = item.get("indications")
            if raw in (None, "", [], {}):
                continue
            ids = raw if isinstance(raw, list) else [raw]
            for unresolved in any_ids_unresolved(ids, data):
                self._add_failure(
                    f"indications references unresolved id {unresolved!r}",
                    "StudyCohort",
                    "indications",
                    data.path_by_id(item["id"]),
                )
        return self._result()
