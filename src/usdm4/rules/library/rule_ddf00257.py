from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00257(RuleTemplate):
    """
    DDF00257: A study design must not be characterized as both "Single Country" and "Multiple Countries".

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: characteristics
    """

    def __init__(self):
        super().__init__(
            "DDF00257",
            RuleTemplate.ERROR,
            'A study design must not be characterized as both "Single Country" and "Multiple Countries".',
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("InterventionalStudyDesign"):
            codes = [
                c.get("code")
                for c in (item.get("characteristics") or [])
                if isinstance(c, dict)
            ]
            if "C217006" in codes and "C217007" in codes:
                self._add_failure(
                    "Incompatible codes C217006 and C217007 both present in characteristics",
                    "InterventionalStudyDesign",
                    "characteristics",
                    data.path_by_id(item["id"]),
                )
        return self._result()
