# MANUAL: do not regenerate
#
# Mutex: a StudyRole must reference either assignedPersons OR
# organizationIds, not both. CORE JSONata filters
# `$sv.roles[assignedPersons and organizationIds]`.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00190(RuleTemplate):
    """
    DDF00190: A study role must not reference both assigned persons and organizations.

    Applies to: StudyRole
    Attributes: assignedPersons, organizations
    """

    def __init__(self):
        super().__init__(
            "DDF00190",
            RuleTemplate.ERROR,
            "A study role must not reference both assigned persons and organizations.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for role in data.instances_by_klass("StudyRole"):
            persons = role.get("assignedPersons") or []
            org_ids = role.get("organizationIds") or []
            if persons and org_ids:
                self._add_failure(
                    f"StudyRole has both assignedPersons ({len(persons)}) and organizationIds ({len(org_ids)})",
                    "StudyRole",
                    "assignedPersons, organizationIds",
                    data.path_by_id(role["id"]),
                )
        return self._result()
