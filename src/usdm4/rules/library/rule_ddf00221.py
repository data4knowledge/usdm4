# MANUAL: do not regenerate
#
# Distinct therapeuticAreas within each study design. Unlike the other
# distinct-within-scope rules, CORE groups by (codeSystem,
# codeSystemVersion, code) — the same code from different systems is
# allowed, but repeating the same full identity is not.
from collections import Counter

from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]


class RuleDDF00221(RuleTemplate):
    """
    DDF00221: Within a study design, if more therapeutic areas are defined, they must be distinct.

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: therapeuticAreas
    """

    def __init__(self):
        super().__init__(
            "DDF00221",
            RuleTemplate.ERROR,
            "Within a study design, if more therapeutic areas are defined, they must be distinct.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for design in data.instances_by_klass(klass):
                entries = design.get("therapeuticAreas") or []
                keys = [
                    (entry.get("codeSystem"), entry.get("codeSystemVersion"), entry.get("code"))
                    for entry in entries
                    if isinstance(entry, dict) and entry.get("code")
                ]
                duplicates = [k for k, n in Counter(keys).items() if n > 1]
                if duplicates:
                    formatted = ", ".join(
                        f"{code} ({cs}@{csv})" for cs, csv, code in duplicates
                    )
                    self._add_failure(
                        f"{klass}.therapeuticAreas has duplicate entry (same codeSystem+version+code): {formatted}",
                        klass,
                        "therapeuticAreas",
                        data.path_by_id(design["id"]),
                    )
        return self._result()
