# MANUAL: do not regenerate
#
# For each double-blind StudyDesign (blindingSchema.standardCode.code
# == C15228), count applicable StudyRoles whose masking.isMasked is
# True. Applicable = appliesToIds contains either the StudyVersion id
# or the StudyDesign id. Fail the design (not the roles) when count < 2.
from usdm4.rules.rule_template import RuleTemplate


DOUBLE_BLIND_CODE = "C15228"


def _blinding_code(design):
    schema = design.get("blindingSchema")
    if not isinstance(schema, dict):
        return None
    standard = schema.get("standardCode")
    if isinstance(standard, dict):
        return standard.get("code")
    return None


class RuleDDF00192(RuleTemplate):
    """
    DDF00192: A masking is expected to be defined for at least two study roles in a study design with a double blind blinding schema.

    Applies to: StudyRole (but failure reported on the StudyDesign)
    Attributes: masking
    """

    def __init__(self):
        super().__init__(
            "DDF00192",
            RuleTemplate.WARNING,
            "A masking is expected to be defined for at least two study roles in a study design with a double blind blinding schema.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            sv_id = sv.get("id")
            for design in sv.get("studyDesigns") or []:
                if not isinstance(design, dict):
                    continue
                if _blinding_code(design) != DOUBLE_BLIND_CODE:
                    continue
                applicable_ids = {sv_id, design.get("id")}
                masked_count = 0
                for role in sv.get("roles") or []:
                    if not isinstance(role, dict):
                        continue
                    applies = role.get("appliesToIds") or []
                    if not any(a in applicable_ids for a in applies):
                        continue
                    masking = role.get("masking")
                    if isinstance(masking, dict) and masking.get("isMasked"):
                        masked_count += 1
                if masked_count < 2:
                    self._add_failure(
                        f"Double-blind StudyDesign has {masked_count} masked applicable StudyRoles (expected at least 2)",
                        "StudyRole",
                        "masking",
                        data.path_by_id(design["id"]),
                    )
        return self._result()
