# MANUAL: do not regenerate
#
# For each StudyDesign (Interventional or Observational), the grid
# { arm × epoch } must be fully covered by StudyCells — exactly one
# StudyCell per (armId, epochId) pair. Missing cells and duplicate
# cells are both failures. Failures reported against the StudyDesign
# with a message listing the missing/duplicate pairs.
from collections import Counter

from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = ["InterventionalStudyDesign", "ObservationalStudyDesign"]


class RuleDDF00243(RuleTemplate):
    """
    DDF00243: Each StudyArm is expected to have one StudyCell for each StudyEpoch.

    Applies to: StudyCell (within each StudyDesign)
    Attributes: armId, epochId
    """

    def __init__(self):
        super().__init__(
            "DDF00243",
            RuleTemplate.WARNING,
            "Each StudyArm is expected to have one StudyCell for each StudyEpoch.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for design in data.instances_by_klass(klass):
                arm_ids = {a.get("id") for a in design.get("arms") or [] if isinstance(a, dict) and a.get("id")}
                epoch_ids = {e.get("id") for e in design.get("epochs") or [] if isinstance(e, dict) and e.get("id")}
                if not (arm_ids and epoch_ids):
                    continue
                cell_counts: Counter = Counter()
                for cell in design.get("studyCells") or []:
                    if not isinstance(cell, dict):
                        continue
                    arm = cell.get("armId")
                    epoch = cell.get("epochId")
                    if arm in arm_ids and epoch in epoch_ids:
                        cell_counts[(arm, epoch)] += 1
                expected = {(a, e) for a in arm_ids for e in epoch_ids}
                missing = expected - set(cell_counts)
                duplicated = {pair for pair, c in cell_counts.items() if c > 1}
                if missing or duplicated:
                    parts = []
                    if missing:
                        parts.append(f"missing arm×epoch cells: {sorted(missing)}")
                    if duplicated:
                        parts.append(f"duplicate arm×epoch cells: {sorted(duplicated)}")
                    self._add_failure(
                        f"{klass}: " + "; ".join(parts),
                        "StudyCell",
                        "armId, epochId",
                        data.path_by_id(design["id"]),
                    )
        return self._result()
