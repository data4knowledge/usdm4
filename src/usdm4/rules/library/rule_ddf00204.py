from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00204(RuleTemplate):
    """
    DDF00204: Narrative content must only reference narrative content that is specified within the same study definition document version.

    Applies to: NarrativeContent
    Attributes: next, previous, children
    """

    def __init__(self):
        super().__init__(
            "DDF00204",
            RuleTemplate.ERROR,
            "Narrative content must only reference narrative content that is specified within the same study definition document version.",
        )

    # GENERATED — predicate inferred from rule text, please review.
    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import any_ids_unresolved
        data = config["data"]
        for item in data.instances_by_klass("NarrativeContent"):
            raw = item.get("next")
            if raw in (None, "", [], {}):
                continue
            ids = raw if isinstance(raw, list) else [raw]
            for unresolved in any_ids_unresolved(ids, data):
                self._add_failure(
                    f"next references unresolved id {unresolved!r}",
                    "NarrativeContent",
                    "next",
                    data.path_by_id(item["id"]),
                )
        return self._result()
