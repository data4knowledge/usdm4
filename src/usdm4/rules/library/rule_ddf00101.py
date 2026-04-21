# MANUAL: do not regenerate
#
# For each Interventional StudyDesign (studyType.code == C98388),
# at least one Procedure within that design's activities must have a
# non-empty `studyInterventionId`. CORE walks
# studyDesigns.activities.definedProcedures and counts procedures
# with a studyInterventionId.
from usdm4.rules.rule_template import RuleTemplate


INTERVENTIONAL_CODE = "C98388"


def _is_interventional(design):
    study_type = design.get("studyType")
    if not isinstance(study_type, dict):
        return False
    return study_type.get("code") == INTERVENTIONAL_CODE


class RuleDDF00101(RuleTemplate):
    """
    DDF00101: Within a study design, if study type is Interventional then at least one intervention is expected to be referenced from a procedure.

    Applies to: Procedure (within InterventionalStudyDesign)
    Attributes: studyInterventionId
    """

    def __init__(self):
        super().__init__(
            "DDF00101",
            RuleTemplate.WARNING,
            "Within a study design, if study type is Interventional then at least one intervention is expected to be referenced from a procedure.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in ("InterventionalStudyDesign", "ObservationalStudyDesign"):
            for design in data.instances_by_klass(klass):
                if not _is_interventional(design):
                    continue
                has_linked_procedure = False
                for activity in design.get("activities") or []:
                    if not isinstance(activity, dict):
                        continue
                    for procedure in activity.get("definedProcedures") or []:
                        if isinstance(procedure, dict) and procedure.get("studyInterventionId"):
                            has_linked_procedure = True
                            break
                    if has_linked_procedure:
                        break
                if not has_linked_procedure:
                    self._add_failure(
                        "Interventional StudyDesign has no Procedure referencing a StudyIntervention",
                        "Procedure",
                        "studyInterventionId",
                        data.path_by_id(design["id"]),
                    )
        return self._result()
