# MANUAL: do not regenerate
#
# For each StudyVersion, each of its roles' `appliesToIds` list must
# either (a) contain exactly one id that is the StudyVersion's own id, or
# (b) be non-empty with every entry being an id of a studyDesign under
# that StudyVersion. Anything else — empty, mixed, or invalid ids — fails.
# Iteration anchors on StudyVersion so we can resolve "my id" and
# "my study designs' ids" without guessing at parent walks per role.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00189(RuleTemplate):
    """
    DDF00189: Every study role must apply to either a study version or at least one study design, but not both.

    Applies to: StudyRole
    Attributes: appliesToIds
    """

    def __init__(self):
        super().__init__(
            "DDF00189",
            RuleTemplate.ERROR,
            "Every study role must apply to either a study version or at least one study design, but not both.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            sv_id = sv.get("id")
            design_ids = {
                d.get("id")
                for d in (sv.get("studyDesigns") or [])
                if isinstance(d, dict) and d.get("id")
            }
            for role in sv.get("roles") or []:
                if not isinstance(role, dict):
                    continue
                ids = role.get("appliesToIds") or []
                valid_version = len(ids) == 1 and ids[0] == sv_id
                valid_design = bool(ids) and all(i in design_ids for i in ids)
                if not (valid_version or valid_design):
                    self._add_failure(
                        "StudyRole does not apply only to the StudyVersion or only to one-or-more of its StudyDesigns",
                        "StudyRole",
                        "appliesToIds",
                        data.path_by_id(role["id"]),
                    )
        return self._result()
