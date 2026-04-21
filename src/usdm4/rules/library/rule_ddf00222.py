# MANUAL: do not regenerate
#
# Twin of DDF00219 on `intentTypes`. Distinct `code` values expected
# within each study design's intentTypes list. YAML `entity` column lists
# InterventionalStudyDesign only but the `scope` block includes both —
# matching the behaviour of DDF00219/20/21.
from collections import Counter

from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]


class RuleDDF00222(RuleTemplate):
    """
    DDF00222: Within a study design, if more intent types are defined, they must be distinct.

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: intentTypes
    """

    def __init__(self):
        super().__init__(
            "DDF00222",
            RuleTemplate.ERROR,
            "Within a study design, if more intent types are defined, they must be distinct.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for design in data.instances_by_klass(klass):
                entries = design.get("intentTypes") or []
                codes = [
                    entry.get("code")
                    for entry in entries
                    if isinstance(entry, dict) and entry.get("code")
                ]
                duplicates = [c for c, n in Counter(codes).items() if n > 1]
                if duplicates:
                    self._add_failure(
                        f"{klass}.intentTypes has duplicate code(s): {', '.join(duplicates)}",
                        klass,
                        "intentTypes",
                        data.path_by_id(design["id"]),
                    )
        return self._result()
