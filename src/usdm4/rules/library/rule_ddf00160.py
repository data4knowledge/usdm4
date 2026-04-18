from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00160(RuleTemplate):
    """
    DDF00160: An activity with children must not refer to a timeline, procedure, biomedical concept, biomedical concept category or biomedical concept surrogate.

    Applies to: Activity
    Attributes: children
    """

    def __init__(self):
        super().__init__(
            "DDF00160",
            RuleTemplate.ERROR,
            "An activity with children must not refer to a timeline, procedure, biomedical concept, biomedical concept category or biomedical concept surrogate.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.studyDesigns)@$sd.
    #       $sd.activities@$p.
    #       $p.
    #         [
    #           (
    #             $ActivityDetails:=(biomedicalConceptIds or bcCategoryIds or definedProcedures
    #               or timelineId or bcSurrogateIds);
    #             $ChkX:=(childIds and $ActivityDetails =true);
    #               {
    #                 "instanceType": $p.instanceType,
    #                 "id": $p.id,
    #                 "path": $p._path,
    #                 "StudyDesign.id": $sd.id,
    #                 "StudyDesign.name": $sd.name,
    #                 "name": $p.name,
    #                 "childIds": $p.childIds,
    #                 "biomedicalConceptIds": $p.biomedicalConceptIds,
    #                 "bcCategoryIds": $p.bcCategoryIds,
    #                 "bcSurrogateIds": $p.bcSurrogateIds,
    #                 "timelineId": $p.timelineId,
    #                 "definedProcedures.id": $p.definedProcedures.id,
    #                 "check": $ChkX
    #               }
    #             )
    #           ]
    #           [check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00160: not yet implemented")
