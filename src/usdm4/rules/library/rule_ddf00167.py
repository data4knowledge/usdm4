from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00167(RuleTemplate):
    """
    DDF00167: A study definition document version must not be referenced more than once by the same study version.

    Applies to: StudyVersion
    Attributes: documentVersions
    """

    def __init__(self):
        super().__init__(
            "DDF00167",
            RuleTemplate.ERROR,
            "A study definition document version must not be referenced more than once by the same study version.",
        )

    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import duplicate_values
        data = config["data"]
        for item in data.instances_by_klass("StudyVersion"):
            dupes = duplicate_values(item.get("documentVersionIds") or [])
            if dupes:
                self._add_failure(
                    f"Duplicate {dupes!r} in documentVersionIds",
                    "StudyVersion",
                    "documentVersionIds",
                    data.path_by_id(item["id"]),
                )
        return self._result()
