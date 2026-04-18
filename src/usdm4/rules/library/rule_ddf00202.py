from usdm4.rules.rule_template import RuleTemplate


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

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions@$sv.
    #       ($sv.roles[code.code = "C70793"])@$r.
    #         $r[$not($count(organizationIds) = 1 and $count($sv.organizations[id in $r.organizationIds]) = 1)].
    #           {
    #             "instanceType": $r.instanceType,
    #             "id": $r.id,
    #             "path": $r._path,
    #             "name": $r.name,
    #             "code": $r.code.decode & " (" & $r.code.code & ")",
    #             "organizationIds": $r.organizationIds
    #               ? "["&$join($r.organizationIds.($oid:=$;$oid&": "&($o:=$sv.organizations[id=$oid];$o?$o.name:"Invalid organizationId")),"; ")&"]",
    #             "# Valid Organizations": $count($sv.organizations[id in $r.organizationIds])
    #           }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00202: not yet implemented")
