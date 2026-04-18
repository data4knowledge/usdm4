from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00252(RuleTemplate):
    """
    DDF00252: A study element must only reference study interventions that are referenced by the same study design as the study element.

    Applies to: StudyElement
    Attributes: studyInterventions
    """

    def __init__(self):
        super().__init__(
            "DDF00252",
            RuleTemplate.ERROR,
            "A study element must only reference study interventions that are referenced by the same study design as the study element.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.versions)@$sv.
    #       $sv.studyDesigns@$sd.
    #               $sd.elements[$count(studyInterventionIds[$not ($ in $sd.studyInterventionIds)])>0].
    #                               {
    #                               "instanceType": instanceType,
    #                               "id": id,
    #                               "path": _path,
    #                               "StudyDesign.id": $sd.id,
    #                               "StudyDesign.name": $sd.name,
    #                               "StudyDesign.studyInterventionIds": $sd.studyInterventionIds,
    #                               "name": name,
    #                               "Invalid studyInterventionIds": studyInterventionIds[$not ($ in $sd.studyInterventionIds)],
    #                               "Invalid StudyIntervention.name": "["&$join(studyInterventionIds[$not ($ in $sd.studyInterventionIds)].($oid:=$;$oid&": "&($o:=$sv.studyInterventions[id=$oid];$o?$o.name:"Not defined")),"; ")&"]"
    #                               }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00252: not yet implemented")
