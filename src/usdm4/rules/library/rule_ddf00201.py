from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00201(RuleTemplate):
    """
    DDF00201: There must be exactly one study role with a code of sponsor.

    Applies to: StudyRole
    Attributes: code
    """

    def __init__(self):
        super().__init__(
            "DDF00201",
            RuleTemplate.ERROR,
            "There must be exactly one study role with a code of sponsor.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions@$sv.
    #       (
    #         $sproles:=$sv.roles[code.code="C70793"];
    #         {
    #           "instanceType": $sv.instanceType,
    #           "id": $sv.id,
    #           "path": $sv._path,
    #           "versionIdentifier": $sv.versionIdentifier,
    #           "# Sponsor Roles": $count($sproles),
    #           "Sponsor Roles": $sproles?"["&$join($sproles.(id&": "&code.decode&"("&code.code&")"),"; ")&"]"
    #         }
    #       )[`# Sponsor Roles` != 1]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00201: not yet implemented")
