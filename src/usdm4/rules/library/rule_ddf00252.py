from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00252(RuleTemplate):
    """
    DDF00252: A study element must only reference study interventions that are referenced by the same study design as the study element.

    Applies to: StudyElement
    Attributes: studyInterventions
    """

    def __init__(self):
        super().__init__(
            "DDF00252",
            RuleTemplate.ERROR,
            "A study element must only reference study interventions that are referenced by the same study design as the study element.",
        )

    # GENERATED — predicate inferred from rule text, please review.
    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import any_ids_unresolved

        data = config["data"]
        for item in data.instances_by_klass("StudyElement"):
            raw = item.get("studyInterventions")
            if raw in (None, "", [], {}):
                continue
            ids = raw if isinstance(raw, list) else [raw]
            for unresolved in any_ids_unresolved(ids, data):
                self._add_failure(
                    f"studyInterventions references unresolved id {unresolved!r}",
                    "StudyElement",
                    "studyInterventions",
                    data.path_by_id(item["id"]),
                )
        return self._result()
