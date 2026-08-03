# MANUAL: do not regenerate
#
# Within each study design, the `characteristics` list must contain
# entries with distinct `code` values. CORE groups by code and flags any
# group whose count is >1.
from collections import Counter

from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]


class RuleDDF00219(RuleTemplate):
    """
    DDF00219: Within a study design, if more characteristics are defined, they must be distinct.

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: characteristics
    """

    def __init__(self):
        super().__init__(
            "DDF00219",
            RuleTemplate.ERROR,
            "Within a study design, if more characteristics are defined, they must be distinct.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for design in data.instances_by_klass(klass):
                entries = design.get("characteristics") or []
                codes = [
                    entry.get("code")
                    for entry in entries
                    if isinstance(entry, dict) and entry.get("code")
                ]
                duplicates = [c for c, n in Counter(codes).items() if n > 1]
                if duplicates:
                    self._add_failure(
                        f"{klass}.characteristics has duplicate code(s): {', '.join(duplicates)}",
                        klass,
                        "characteristics",
                        data.path_by_id(design["id"]),
                    )
        return self._result()
