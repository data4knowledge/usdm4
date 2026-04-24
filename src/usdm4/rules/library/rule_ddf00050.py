from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00050(RuleTemplate):
    """
    DDF00050: A study arm must only reference study populations or cohorts that are defined within the same study design as the study arm.

    Applies to: StudyArm
    Attributes: populations
    """

    def __init__(self):
        super().__init__(
            "DDF00050",
            RuleTemplate.ERROR,
            "A study arm must only reference study populations or cohorts that are defined within the same study design as the study arm.",
        )

    # GENERATED — predicate inferred from rule text, please review.
    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import any_ids_unresolved

        data = config["data"]
        for item in data.instances_by_klass("StudyArm"):
            raw = item.get("populations")
            if raw in (None, "", [], {}):
                continue
            ids = raw if isinstance(raw, list) else [raw]
            for unresolved in any_ids_unresolved(ids, data):
                self._add_failure(
                    f"populations references unresolved id {unresolved!r}",
                    "StudyArm",
                    "populations",
                    data.path_by_id(item["id"]),
                )
        return self._result()
