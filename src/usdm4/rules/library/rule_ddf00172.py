# MANUAL: do not regenerate
#
# Auto-classified as LOW_CUSTOM by stage-1 — CORE's JSONata uses an
# in-expression variable (`$spIds :=`) plus a count-comparison filter that
# doesn't fit any translator pattern. Hand-authored.
#
# Field names verified against dataStructure.yml:
#   StudyVersion.studyIdentifiers   (embedded, 1..*)
#   StudyVersion.roles              (embedded, 0..*)
#   StudyRole.code                  (embedded Code, 1)
#   StudyRole.organizationIds       (id list, 0..*)
#   StudyIdentifier.scopeId         (single id, 1)
#
# "Sponsor" role is identified by CDISC code C70793.
from usdm4.rules.rule_template import RuleTemplate


SPONSOR_ROLE_CODE = "C70793"


class RuleDDF00172(RuleTemplate):
    """
    DDF00172: There must be exactly one sponsor study identifier (i.e., a
    study identifier whose scope is an organization that is identified as
    the organization for the sponsor study role).

    Applies to: StudyIdentifier
    Attributes: scope
    """

    def __init__(self):
        super().__init__(
            "DDF00172",
            RuleTemplate.ERROR,
            "There must be exactly one sponsor study identifier (i.e., a study identifier whose scope is an organization that is identified as the organization for the sponsor study role).",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            # Organisations fulfilling the sponsor role within this StudyVersion
            sponsor_org_ids: set[str] = set()
            for role in sv.get("roles") or []:
                code = role.get("code") or {}
                if isinstance(code, dict) and code.get("code") == SPONSOR_ROLE_CODE:
                    for oid in role.get("organizationIds") or []:
                        sponsor_org_ids.add(oid)

            # Study identifiers whose scope is a sponsor organisation
            sponsor_identifier_count = sum(
                1
                for ident in (sv.get("studyIdentifiers") or [])
                if ident.get("scopeId") in sponsor_org_ids
            )

            if sponsor_identifier_count != 1:
                self._add_failure(
                    f"Expected exactly one sponsor study identifier, found {sponsor_identifier_count}",
                    "StudyVersion",
                    "studyIdentifiers",
                    data.path_by_id(sv["id"]),
                )
        return self._result()
