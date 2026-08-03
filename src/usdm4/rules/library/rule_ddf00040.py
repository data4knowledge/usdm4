# MANUAL: do not regenerate
#
# Each StudyElement must be referenced by at least one StudyCell via
# StudyCell.elementIds. The previous implementation iterated
# StudyElement instances and looked for a non-existent `elements`
# attribute on them (StudyElement has `studyInterventionIds`,
# `transitionEndRule`, etc. — there is no `elements`), which meant
# every element was flagged as "missing elements" regardless of
# whether any cell referenced it.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00040(RuleTemplate):
    """
    DDF00040: Each study element must be referenced by at least one study cell.

    Applies to: StudyCell
    Attributes: elements
    """

    def __init__(self):
        super().__init__(
            "DDF00040",
            RuleTemplate.ERROR,
            "Each study element must be referenced by at least one study cell.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        referenced: set[str] = set()
        for cell in data.instances_by_klass("StudyCell"):
            for eid in cell.get("elementIds") or []:
                if isinstance(eid, str) and eid:
                    referenced.add(eid)

        for element in data.instances_by_klass("StudyElement"):
            eid = element.get("id")
            if eid and eid not in referenced:
                self._add_failure(
                    f"StudyElement {eid!r} is not referenced by any StudyCell.elementIds",
                    "StudyElement",
                    "id",
                    data.path_by_id(eid),
                )
        return self._result()
