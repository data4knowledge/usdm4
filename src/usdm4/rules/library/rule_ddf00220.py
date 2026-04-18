# MANUAL: do not regenerate
#
# Twin of DDF00219 on `subTypes`. Distinct `code` values expected within
# each study design's subTypes list.
from collections import Counter

from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]


class RuleDDF00220(RuleTemplate):
    """
    DDF00220: Within a study design, if more sub types are defined, they must be distinct.

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: subTypes
    """

    def __init__(self):
        super().__init__(
            "DDF00220",
            RuleTemplate.ERROR,
            "Within a study design, if more sub types are defined, they must be distinct.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for design in data.instances_by_klass(klass):
                entries = design.get("subTypes") or []
                codes = [
                    entry.get("code")
                    for entry in entries
                    if isinstance(entry, dict) and entry.get("code")
                ]
                duplicates = [c for c, n in Counter(codes).items() if n > 1]
                if duplicates:
                    self._add_failure(
                        f"{klass}.subTypes has duplicate code(s): {', '.join(duplicates)}",
                        klass,
                        "subTypes",
                        data.path_by_id(design["id"]),
                    )
        return self._result()
