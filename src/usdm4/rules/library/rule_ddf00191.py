from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00191(RuleTemplate):
    """
    DDF00191: A masking is not expected to be defined for any study role in a study design with an open label blinding schema.

    Applies to: StudyRole
    Attributes: masking
    """

    def __init__(self):
        super().__init__(
            "DDF00191",
            RuleTemplate.WARNING,
            "A masking is not expected to be defined for any study role in a study design with an open label blinding schema.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     $.study.versions@$sv.
    #       [
    #         ($sv.roles)@$r.($sv.studyDesigns)@$sd
    #           [
    #             (
    #                 $sv.id in $r.appliesToIds or
    #                 $sd.id in $r.appliesToIds
    #             ) and
    #             $r.masking.isMasked and
    #             $sd.blindingSchema.standardCode.code = "C49659"
    #           ].{
    #               "instanceType": $r.instanceType,
    #               "id": $r.id,
    #               "path": $r._path,
    #               "name": $r.name,
    #               "code": $r.code.decode,
    #               "masking.text": $r.masking.text,
    #               "masking.isMasked": $r.masking.isMasked,
    #               "appliesToIds": $r.appliesToIds,
    #               "StudyDesign.id": $sd.id,
    #               "StudyDesign.name": $sd.name,
    #               "StudyDesign.blindingSchema": $sd.blindingSchema.standardCode.decode
    #             }
    #       ]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00191: not yet implemented")
