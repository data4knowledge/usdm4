from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00072(RuleTemplate):
    """
    DDF00072: A study cell must only reference an epoch that is defined within the same study design as the study cell.

    Applies to: StudyCell
    Attributes: epoch
    """

    def __init__(self):
        super().__init__(
            "DDF00072",
            RuleTemplate.ERROR,
            "A study cell must only reference an epoch that is defined within the same study design as the study cell.",
        )

    # GENERATED — predicate inferred from rule text, please review.
    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import any_ids_unresolved

        data = config["data"]
        for item in data.instances_by_klass("StudyCell"):
            raw = item.get("epoch")
            if raw in (None, "", [], {}):
                continue
            ids = raw if isinstance(raw, list) else [raw]
            for unresolved in any_ids_unresolved(ids, data):
                self._add_failure(
                    f"epoch references unresolved id {unresolved!r}",
                    "StudyCell",
                    "epoch",
                    data.path_by_id(item["id"]),
                )
        return self._result()
