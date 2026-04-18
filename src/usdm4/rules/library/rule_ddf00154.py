from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00154(RuleTemplate):
    """
    DDF00154: A study design must not be characterized as both "Single-Centre" and "Multicentre".

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: characteristics
    """

    def __init__(self):
        super().__init__(
            "DDF00154",
            RuleTemplate.ERROR,
            'A study design must not be characterized as both "Single-Centre" and "Multicentre".',
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("InterventionalStudyDesign"):
            codes = [c.get("code") for c in (item.get("characteristics") or []) if isinstance(c, dict)]
            if "C217004" in codes and "C217005" in codes:
                self._add_failure(
                    f"Incompatible codes C217004 and C217005 both present in characteristics",
                    "InterventionalStudyDesign",
                    "characteristics",
                    data.path_by_id(item["id"]),
                )
        return self._result()
