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

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions@$sv.
    #       ($sv.roles[assignedPersons and organizationIds])@$r.
    #         {
    #           "instanceType": $r.instanceType,
    #           "id": $r.id,
    #           "path": $r._path,
    #           "name": $r.name,
    #           "code": $r.code.decode & " (" & $r.code.code & ")",
    #           "assignedPersons": "["&$join($r.assignedPersons.(id&": "&name),"; ")&"]",
    #           "organizationIds": "["&$join($r.organizationIds.($oid:=$;$oid&": "&($o:=$sv.organizations[id=$oid];$o?$o.name:"Invalid organizationId")),"; ")&"]"
    #         }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00190: not yet implemented")
