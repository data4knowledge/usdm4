# MANUAL: do not regenerate
#
# For each StudyVersion, find StudyDesigns with open-label blinding
# schema (AliasCode.standardCode.code == C49659). For each such
# StudyDesign, walk the StudyVersion's roles; any role whose
# appliesToIds includes the SV id OR the StudyDesign id AND that has
# masking.isMasked == True is a failure.
from usdm4.rules.rule_template import RuleTemplate


OPEN_LABEL_CODE = "C49659"


def _blinding_code(design):
    schema = design.get("blindingSchema")
    if not isinstance(schema, dict):
        return None
    standard = schema.get("standardCode")
    if isinstance(standard, dict):
        return standard.get("code")
    return None


class RuleDDF00191(RuleTemplate):
    """
    DDF00191: A masking is not expected to be defined for any study role in a study design with an open label blinding schema.

    Applies to: StudyRole
    Attributes: masking
    """

    def __init__(self):
        super().__init__(
            "DDF00191",
            RuleTemplate.WARNING,
            "A masking is not expected to be defined for any study role in a study design with an open label blinding schema.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            sv_id = sv.get("id")
            open_label_designs = [
                d for d in (sv.get("studyDesigns") or [])
                if isinstance(d, dict) and _blinding_code(d) == OPEN_LABEL_CODE
            ]
            if not open_label_designs:
                continue
            applicable_ids = {sv_id} | {d.get("id") for d in open_label_designs}
            for role in sv.get("roles") or []:
                if not isinstance(role, dict):
                    continue
                applies = role.get("appliesToIds") or []
                if not any(a in applicable_ids for a in applies):
                    continue
                masking = role.get("masking")
                if isinstance(masking, dict) and masking.get("isMasked"):
                    self._add_failure(
                        "StudyRole has masking but applies to an open-label StudyDesign",
                        "StudyRole",
                        "masking",
                        data.path_by_id(role["id"]),
                    )
        return self._result()
