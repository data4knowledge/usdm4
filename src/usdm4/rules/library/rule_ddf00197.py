from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00197(RuleTemplate):
    """
    DDF00197: A study definition document version must not be referenced more than once by the same study design.

    Applies to: ObservationalStudyDesign, InterventionalStudyDesign
    Attributes: documentVersions
    """

    def __init__(self):
        super().__init__(
            "DDF00197",
            RuleTemplate.WARNING,
            "A study definition document version must not be referenced more than once by the same study design.",
        )

    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import duplicate_values

        data = config["data"]
        for item in data.instances_by_klass("InterventionalStudyDesign"):
            dupes = duplicate_values(item.get("documentVersionIds") or [])
            if dupes:
                self._add_failure(
                    f"Duplicate {dupes!r} in documentVersionIds",
                    "InterventionalStudyDesign",
                    "documentVersionIds",
                    data.path_by_id(item["id"]),
                )
        return self._result()
