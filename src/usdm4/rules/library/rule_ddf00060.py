from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00060(RuleTemplate):
    """
    DDF00060: The value for each timing must be a non-negative duration specified in ISO 8601 format.

    Applies to: Timing
    Attributes: value
    """

    def __init__(self):
        super().__init__(
            "DDF00060",
            RuleTemplate.ERROR,
            "The value for each timing must be a non-negative duration specified in ISO 8601 format.",
        )

    def validate(self, config: dict) -> bool:
        import re
        # ISO 8601 duration — optional leading "-" (negative), but CORE convention
        # requires non-negative here. Anchors at start/end.
        pat = re.compile(
            r"^P(?!$)(\d+(?:\.\d+)?Y)?(\d+(?:\.\d+)?M)?(\d+(?:\.\d+)?W)?(\d+(?:\.\d+)?D)?"
            r"(T(\d+(?:\.\d+)?H)?(\d+(?:\.\d+)?M)?(\d+(?:\.\d+)?S)?)?$"
        )
        data = config["data"]
        for item in data.instances_by_klass("Timing"):
            v = item.get("value")
            if not v:
                continue
            if not pat.match(str(v)):
                self._add_failure(
                    f"'{v}' is not a non-negative ISO 8601 duration",
                    "Timing",
                    "value",
                    data.path_by_id(item["id"]),
                )
        return self._result()
