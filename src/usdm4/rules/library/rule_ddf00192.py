from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00192(RuleTemplate):
    """
    DDF00192: A masking is expected to be defined for at least two study roles in a study design with a double blind blinding schema.

    Applies to: StudyRole
    Attributes: masking
    """

    def __init__(self):
        super().__init__(
            "DDF00192",
            RuleTemplate.WARNING,
            "A masking is expected to be defined for at least two study roles in a study design with a double blind blinding schema.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.study.versions)@$sv.
    #       ($sv.studyDesigns)@$sd
    #         [
    #           $sd.blindingSchema.standardCode.code = "C15228"
    #         ].[
    #             ( 
    #               $maskedRoles := $sv.roles@$r
    #                                 [
    #                                   $sv.id in $r.appliesToIds or
    #                                   $sd.id in $r.appliesToIds
    #                                 ].{
    #                                     "id": $r.id,
    #                                     "code": $r.code.decode,
    #                                     "isMasked": $r.masking.isMasked
    #                                   };
    #               {
    #                 "instanceType": $sd.instanceType,
    #                 "id": $sd.id,
    #                 "path": $sd._path,
    #                 "name": $sd.name,
    #                 "blindingSchema.code": $sd.blindingSchema.standardCode.code,
    #                 "blindingSchema.decode": $sd.blindingSchema.standardCode.decode,
    #                 "# Masked Roles": $count($maskedRoles[isMasked=true]),
    #                 "Applicable Roles":
    #                   $maskedRoles
    #                   ~>  $map(function($v)
    #                         {$join([$v.code,'[',$v.id,',',$v.isMasked=true?'Masked':'Not Masked',']'])}
    #                       )
    #                   ~> $join("; ")
    #               }
    #             )
    #           ][`# Masked Roles` < 2]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00192: not yet implemented")
