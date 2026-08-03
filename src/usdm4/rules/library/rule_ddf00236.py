# MANUAL: do not regenerate
#
# For each BiomedicalConcept, no entry in `synonyms` (case-insensitive)
# may equal its `label`. synonyms is a list of strings on BC in USDM.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00236(RuleTemplate):
    """
    DDF00236: If a synonym is specified then it is not expected to be equal to the label of the biomedical concept (case insensitive).

    Applies to: BiomedicalConcept
    Attributes: synonyms
    """

    def __init__(self):
        super().__init__(
            "DDF00236",
            RuleTemplate.WARNING,
            "If a synonym is specified then it is not expected to be equal to the label of the biomedical concept (case insensitive).",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for bc in data.instances_by_klass("BiomedicalConcept"):
            label = bc.get("label")
            synonyms = bc.get("synonyms") or []
            if not isinstance(label, str) or not label:
                continue
            label_lower = label.lower()
            for synonym in synonyms:
                if isinstance(synonym, str) and synonym.lower() == label_lower:
                    self._add_failure(
                        f"BiomedicalConcept synonym {synonym!r} equals the label (case-insensitive)",
                        "BiomedicalConcept",
                        "synonyms",
                        data.path_by_id(bc["id"]),
                    )
                    break
        return self._result()
