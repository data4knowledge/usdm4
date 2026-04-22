from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00062(RuleTemplate):
    """
    DDF00062: When specified, the upper limit of a timing window must be a non-negative duration in ISO 8601 format.

    Applies to: Timing
    Attributes: windowUpper
    """

    def __init__(self):
        super().__init__(
            "DDF00062",
            RuleTemplate.ERROR,
            "When specified, the upper limit of a timing window must be a non-negative duration in ISO 8601 format.",
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
            v = item.get("windowUpper")
            if not v:
                continue
            if not pat.match(str(v)):
                self._add_failure(
                    f"'{v}' is not a non-negative ISO 8601 duration",
                    "Timing",
                    "windowUpper",
                    data.path_by_id(item["id"]),
                )
        return self._result()
