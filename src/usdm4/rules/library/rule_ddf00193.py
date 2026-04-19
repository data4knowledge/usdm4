# MANUAL: do not regenerate
#
# For each StudyDesign whose blindingSchema is neither Open Label
# (C49659) nor Double Blind (C15228), at least one applicable
# StudyRole (i.e. a role with the SV id or the SD id in its
# appliesToIds) must have masking.isMasked == True.
# DDF00191 and DDF00192 cover the open-label and double-blind cases.
from usdm4.rules.rule_template import RuleTemplate


OPEN_LABEL_CODE = "C49659"
DOUBLE_BLIND_CODE = "C15228"


def _blinding_code(design):
    schema = design.get("blindingSchema")
    if not isinstance(schema, dict):
        return None
    standard = schema.get("standardCode")
    if isinstance(standard, dict):
        return standard.get("code")
    return None


class RuleDDF00193(RuleTemplate):
    """
    DDF00193: A masking is expected to be defined for at least one study role in a study design with a blinding schema that is not open label or double blind.

    Applies to: StudyRole (scoped to StudyDesigns with non-open-label / non-double-blind blinding)
    Attributes: masking
    """

    def __init__(self):
        super().__init__(
            "DDF00193",
            RuleTemplate.WARNING,
            "A masking is expected to be defined for at least one study role in a study design with a blinding schema that is not open label or double blind.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            sv_id = sv.get("id")
            for design in sv.get("studyDesigns") or []:
                if not isinstance(design, dict):
                    continue
                code = _blinding_code(design)
                if code is None or code in (OPEN_LABEL_CODE, DOUBLE_BLIND_CODE):
                    continue
                applicable_ids = {sv_id, design.get("id")}
                has_masked_role = False
                for role in sv.get("roles") or []:
                    if not isinstance(role, dict):
                        continue
                    applies = role.get("appliesToIds") or []
                    if not any(a in applicable_ids for a in applies):
                        continue
                    masking = role.get("masking")
                    if isinstance(masking, dict) and masking.get("isMasked"):
                        has_masked_role = True
                        break
                if not has_masked_role:
                    self._add_failure(
                        f"StudyDesign with blinding schema {code} has no applicable StudyRole with masking",
                        "StudyRole",
                        "masking",
                        data.path_by_id(design["id"]),
                    )
        return self._result()
