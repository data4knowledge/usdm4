from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00172(RuleTemplate):
    """
    DDF00172: There must be exactly one sponsor study identifier (i.e., a study identifier whose scope is an organization that is identified as the organization for the sponsor study role).

    Applies to: StudyIdentifier
    Attributes: scope
    """

    def __init__(self):
        super().__init__(
            "DDF00172",
            RuleTemplate.ERROR,
            "There must be exactly one sponsor study identifier (i.e., a study identifier whose scope is an organization that is identified as the organization for the sponsor study role).",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     [$.study.versions@$sv.
    #       (
    #         $spIds := $sv.studyIdentifiers[scopeId in $sv.roles[code.code="C70793"].organizationIds];
    #         {
    #           "instanceType": $sv.instanceType,
    #           "id": $sv.id,
    #           "path": $sv._path,
    #           "versionIdentifier": $sv.versionIdentifier,
    #           "# Sponsor Identifiers": $count($spIds),
    #           "Sponsor Identifiers": $spIds.
    #             (
    #               $spid:=$;
    #               $spid.id & ": " & $spid.text & " (" & $spid.scopeId & 
    #                 ": " & $sv.organizations[id=$spid.scopeId].name & ")"
    #             )
    #         }
    #       )][`# Sponsor Identifiers` != 1]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00172: not yet implemented")
