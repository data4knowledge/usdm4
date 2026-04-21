from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00038(RuleTemplate):
    """
    DDF00038: A scheduled decision instance must refer to a default condition.

    Applies to: ScheduledDecisionInstance
    Attributes: defaultCondition
    """

    def __init__(self):
        super().__init__(
            "DDF00038",
            RuleTemplate.ERROR,
            "A scheduled decision instance must refer to a default condition.",
        )

    # GENERATED — predicate inferred from rule text, please review.
    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import any_ids_unresolved
        data = config["data"]
        for item in data.instances_by_klass("ScheduledDecisionInstance"):
            raw = item.get("defaultCondition")
            if raw in (None, "", [], {}):
                continue
            ids = raw if isinstance(raw, list) else [raw]
            for unresolved in any_ids_unresolved(ids, data):
                self._add_failure(
                    f"defaultCondition references unresolved id {unresolved!r}",
                    "ScheduledDecisionInstance",
                    "defaultCondition",
                    data.path_by_id(item["id"]),
                )
        return self._result()
