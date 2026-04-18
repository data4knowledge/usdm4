# MANUAL: do not regenerate
#
# For each sponsor StudyRole, organizationIds must have exactly 1 entry AND
# that entry must resolve to an organisation within the same StudyVersion.
# CORE's JSONata checks `$count(organizationIds) = 1` and `$count(organizations
# where id matches) = 1`. The second test catches the case where
# organizationIds has one element but it doesn't exist.
from usdm4.rules.rule_template import RuleTemplate


SPONSOR_ROLE_CODE = "C70793"


class RuleDDF00202(RuleTemplate):
    """
    DDF00202: The sponsor study role must point to exactly one organization.

    Applies to: StudyRole
    Attributes: organizations
    """

    def __init__(self):
        super().__init__(
            "DDF00202",
            RuleTemplate.ERROR,
            "The sponsor study role must point to exactly one organization.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            sv_org_ids = {
                o["id"] for o in sv.get("organizations") or [] if isinstance(o, dict) and "id" in o
            }
            for role in sv.get("roles") or []:
                code = role.get("code") or {}
                if not (isinstance(code, dict) and code.get("code") == SPONSOR_ROLE_CODE):
                    continue
                org_ids = role.get("organizationIds") or []
                matching = [oid for oid in org_ids if oid in sv_org_ids]
                if len(org_ids) != 1 or len(matching) != 1:
                    self._add_failure(
                        f"Sponsor StudyRole must point to exactly one organization "
                        f"(found {len(org_ids)} id(s), {len(matching)} matching in this StudyVersion)",
                        "StudyRole",
                        "organizationIds",
                        data.path_by_id(role["id"]),
                    )
        return self._result()
