from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00168(RuleTemplate):
    """
    DDF00168: A piece of narrative content must only reference narrative content items that have been defined within the study version as the narrative content.

    Applies to: NarrativeContent
    Attributes: contentItem
    """

    def __init__(self):
        super().__init__(
            "DDF00168",
            RuleTemplate.ERROR,
            "A piece of narrative content must only reference narrative content items that have been defined within the study version as the narrative content.",
        )

    # GENERATED — predicate inferred from rule text, please review.
    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import any_ids_unresolved

        data = config["data"]
        for item in data.instances_by_klass("NarrativeContent"):
            raw = item.get("contentItem")
            if raw in (None, "", [], {}):
                continue
            ids = raw if isinstance(raw, list) else [raw]
            for unresolved in any_ids_unresolved(ids, data):
                self._add_failure(
                    f"contentItem references unresolved id {unresolved!r}",
                    "NarrativeContent",
                    "contentItem",
                    data.path_by_id(item["id"]),
                )
        return self._result()
