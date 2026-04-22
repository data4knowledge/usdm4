from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00102(RuleTemplate):
    """
    DDF00102: A scheduled activity instance must only reference a timeline exit that is defined within the same schedule timeline as the scheduled activity instance.

    Applies to: ScheduledActivityInstance
    Attributes: timelineExit
    """

    def __init__(self):
        super().__init__(
            "DDF00102",
            RuleTemplate.ERROR,
            "A scheduled activity instance must only reference a timeline exit that is defined within the same schedule timeline as the scheduled activity instance.",
        )

    # GENERATED — predicate inferred from rule text, please review.
    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import any_ids_unresolved

        data = config["data"]
        for item in data.instances_by_klass("ScheduledActivityInstance"):
            raw = item.get("timelineExit")
            if raw in (None, "", [], {}):
                continue
            ids = raw if isinstance(raw, list) else [raw]
            for unresolved in any_ids_unresolved(ids, data):
                self._add_failure(
                    f"timelineExit references unresolved id {unresolved!r}",
                    "ScheduledActivityInstance",
                    "timelineExit",
                    data.path_by_id(item["id"]),
                )
        return self._result()
