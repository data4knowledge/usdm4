# MANUAL: do not regenerate
#
# CORE flags Interventional StudyDesigns whose model.code is one of
# {C82637 Parallel, C82639 Factorial, C82638 Crossover} — i.e.
# multi-group designs — AND whose distinct studyInterventionIds count
# is <= 1. The "single group" half of the rule text is not checked by
# CORE; we mirror CORE's behaviour.
from usdm4.rules.rule_template import RuleTemplate


INTERVENTIONAL_CODE = "C98388"
MULTI_GROUP_MODEL_CODES = {"C82637", "C82639", "C82638"}


class RuleDDF00213(RuleTemplate):
    """
    DDF00213: If the intervention model indicates a single group design then only one intervention is expected. In all other cases more interventions are expected.

    Applies to: InterventionalStudyDesign
    Attributes: model, studyInterventionIds
    """

    def __init__(self):
        super().__init__(
            "DDF00213",
            RuleTemplate.WARNING,
            "If the intervention model indicates a single group design then only one intervention is expected. In all other cases more interventions are expected.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            known_intervention_ids = {
                si.get("id")
                for si in sv.get("studyInterventions") or []
                if isinstance(si, dict) and si.get("id")
            }
            for design in sv.get("studyDesigns") or []:
                if not isinstance(design, dict):
                    continue
                study_type = design.get("studyType")
                if not (
                    isinstance(study_type, dict)
                    and study_type.get("code") == INTERVENTIONAL_CODE
                ):
                    continue
                model = design.get("model")
                model_code = model.get("code") if isinstance(model, dict) else None
                if model_code not in MULTI_GROUP_MODEL_CODES:
                    continue
                referenced = {
                    i
                    for i in design.get("studyInterventionIds") or []
                    if i in known_intervention_ids
                }
                if len(referenced) <= 1:
                    self._add_failure(
                        f"Multi-group InterventionalStudyDesign (model {model_code}) references {len(referenced)} intervention(s); expected more than 1",
                        "InterventionalStudyDesign",
                        "model, studyInterventionIds",
                        data.path_by_id(design["id"]),
                    )
        return self._result()
