from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00101(RuleTemplate):
    """
    DDF00101: Within a study design, if study type is Interventional then at least one intervention is expected to be referenced from a procedure.

    Applies to: Procedure
    Attributes: studyIntervention
    """

    def __init__(self):
        super().__init__(
            "DDF00101",
            RuleTemplate.WARNING,
            "Within a study design, if study type is Interventional then at least one intervention is expected to be referenced from a procedure.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.study.versions[$not("studyType" in $keys($)) or studyType.code = "C98388"])@$sv.
    #       ($sv.studyDesigns[$not("studyType" in $keys($)) or studyType.code = "C98388"])@$sd.
    #         {
    #           "instanceType": $sd.instanceType,
    #           "id": $sd.id,
    #           "path": $sd._path,
    #           "name": $sd.name,
    #           "studyType.code": $append($sv.studyType.code,$sd.studyType.code),
    #           "studyType.decode": $append($sv.studyType.decode,$sd.studyType.decode),
    #           "# Referenced Study Interventions":
    #               $count($sd.activities.definedProcedures
    #                 [
    #                   studyInterventionId in
    #                     $append($sd.studyInterventionIds[$ in $sv.studyInterventions.id],$sd.studyInterventions.id)
    #                 ]
    #               )
    #         }[`# Referenced Study Interventions` < 1][]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00101: not yet implemented")
