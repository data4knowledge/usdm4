# MANUAL: do not regenerate
#
# Set-intersection check: count entries in characteristics whose code is
# one of {C46079 Randomized, C25689 Stratification, C147145 Stratified
# Randomisation}. If >1, fail. CORE filters by `code in [...]` and counts.
from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]
RANDOMIZATION_CODES = {"C46079", "C25689", "C147145"}


class RuleDDF00258(RuleTemplate):
    """
    DDF00258: A study design is not expected to have more than one of the following characteristics: "Randomized", "Stratification", "Stratified Randomisation".

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: characteristics
    """

    def __init__(self):
        super().__init__(
            "DDF00258",
            RuleTemplate.WARNING,
            'A study design is not expected to have more than one of the following characteristics: "Randomized", "Stratification", "Stratified Randomisation".',
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for design in data.instances_by_klass(klass):
                entries = design.get("characteristics") or []
                hits = [
                    entry.get("code")
                    for entry in entries
                    if isinstance(entry, dict)
                    and entry.get("code") in RANDOMIZATION_CODES
                ]
                if len(hits) > 1:
                    self._add_failure(
                        f"{klass} has {len(hits)} characteristics from the randomisation set: {', '.join(hits)}",
                        klass,
                        "characteristics",
                        data.path_by_id(design["id"]),
                    )
        return self._result()
