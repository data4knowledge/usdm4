from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00193(RuleTemplate):
    """
    DDF00193: A masking is expected to be defined for at least one study role in a study design with a blinding schema that is not open label or double blind.

    Applies to: StudyRole
    Attributes: masking
    """

    def __init__(self):
        super().__init__(
            "DDF00193",
            RuleTemplate.WARNING,
            "A masking is expected to be defined for at least one study role in a study design with a blinding schema that is not open label or double blind.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.study.versions)@$sv.
    #       ($sv.studyDesigns)@$sd
    #         [ 
    #           $sd.blindingSchema and
    #           $not($sd.blindingSchema.standardCode.code in ["C49659","C15228"])
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
    #           ][`# Masked Roles` < 1]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00193: not yet implemented")
