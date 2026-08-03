from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00240(RuleTemplate):
    """
    DDF00240: A procedure must only reference a study intervention that is referenced by the same study design as the activity within which the procedure is defined.

    Applies to: Procedure
    Attributes: studyIntervention
    """

    def __init__(self):
        super().__init__(
            "DDF00240",
            RuleTemplate.ERROR,
            "A procedure must only reference a study intervention that is referenced by the same study design as the activity within which the procedure is defined.",
        )

    # GENERATED — predicate inferred from rule text, please review.
    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import any_ids_unresolved

        data = config["data"]
        for item in data.instances_by_klass("Procedure"):
            raw = item.get("studyIntervention")
            if raw in (None, "", [], {}):
                continue
            ids = raw if isinstance(raw, list) else [raw]
            for unresolved in any_ids_unresolved(ids, data):
                self._add_failure(
                    f"studyIntervention references unresolved id {unresolved!r}",
                    "Procedure",
                    "studyIntervention",
                    data.path_by_id(item["id"]),
                )
        return self._result()
