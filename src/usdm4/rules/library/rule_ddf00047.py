# MANUAL: do not regenerate
#
# StudyCell.elementIds must resolve to StudyElement instances that live
# under the same StudyDesign as the StudyCell.
from usdm4.rules.rule_template import RuleTemplate


STUDY_DESIGN_KLASSES = [
    "StudyDesign",
    "InterventionalStudyDesign",
    "ObservationalStudyDesign",
]


class RuleDDF00047(RuleTemplate):
    """
    DDF00047: A study cell must only reference elements that are defined within the same study design as the study cell.

    Applies to: StudyCell
    Attributes: elementIds
    """

    def __init__(self):
        super().__init__(
            "DDF00047",
            RuleTemplate.ERROR,
            "A study cell must only reference elements that are defined within the same study design as the study cell.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for cell in data.instances_by_klass("StudyCell"):
            cell_design = data.parent_by_klass(cell.get("id"), STUDY_DESIGN_KLASSES)
            if cell_design is None:
                continue
            for element_id in cell.get("elementIds") or []:
                if not element_id:
                    continue
                element_design = data.parent_by_klass(element_id, STUDY_DESIGN_KLASSES)
                if element_design is None:
                    continue
                if element_design.get("id") != cell_design.get("id"):
                    self._add_failure(
                        f"StudyCell.elementIds entry {element_id!r} is defined under a different StudyDesign",
                        "StudyCell",
                        "elementIds",
                        data.path_by_id(cell["id"]),
                    )
        return self._result()
