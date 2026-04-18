from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00240(RuleTemplate):
    """
    DDF00240: A procedure must only reference a study intervention that is referenced by the same study design as the activity within which the procedure is defined.

    Applies to: Procedure
    Attributes: studyIntervention
    """

    def __init__(self):
        super().__init__(
            "DDF00240",
            RuleTemplate.ERROR,
            "A procedure must only reference a study intervention that is referenced by the same study design as the activity within which the procedure is defined.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions)@$sv.
    #       $sv.studyDesigns@$sd.
    #       $sd.activities@$sa.
    #       $sa.definedProcedures@$sp.
    #       $sp.
    #           [studyInterventionId[$ and $not($ in $sd.studyInterventionIds)].
    #               {
    #                   "instanceType": $sp.instanceType,
    #                   "id": $sp.id,
    #                   "path": $sp._path,
    #                   "StudyDesign.id": $sd.id,
    #                   "StudyDesign.name": $sd.name,
    #                   "StudyDesign.studyInterventionIds": $sd.studyInterventionIds,
    #                   "Activity.id": $sa.id,
    #                   "Activity.name": $sa.name,
    #                   "name": $sp.name,
    #                   "studyInterventionId": $sp.studyInterventionId,
    #                   "StudyIntervention.name": $sv.studyInterventions[id=$sp.studyInterventionId].name 
    #               }]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00240: not yet implemented")
