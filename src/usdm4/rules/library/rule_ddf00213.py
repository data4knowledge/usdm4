from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00213(RuleTemplate):
    """
    DDF00213: If the intervention model indicates a single group design then only one intervention is expected. In all other cases more interventions are expected.

    Applies to: InterventionalStudyDesign
    Attributes: model
    """

    def __init__(self):
        super().__init__(
            "DDF00213",
            RuleTemplate.WARNING,
            "If the intervention model indicates a single group design then only one intervention is expected. In all other cases more interventions are expected.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.study.versions)@$sv.
    #       ($sv.studyDesigns[studyType.code = "C98388"])@$sd.
    #         {
    #           "instanceType": $sd.instanceType,
    #           "id": $sd.id,
    #           "path": $sd._path,
    #           "name": $sd.name,
    #           "studyType.code": $sd.studyType.code,
    #           "studyType.decode": $sd.studyType.decode,
    #           "model.code": $sd.model.code,
    #           "model.decode": $sd.model.decode,
    #           "# Referenced Study Interventions":  $count($distinct($sd.studyInterventionIds[$ in $sv.studyInterventions.id]))
    #         }
    #         [
    #           (`model.code` in ["C82637","C82639","C82638"] and `# Referenced Study Interventions` <= 1)
    #         ]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00213: not yet implemented")
