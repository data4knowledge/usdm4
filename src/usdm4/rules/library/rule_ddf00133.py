from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00133(RuleTemplate):
    """
    DDF00133: Within a study design, if a planned enrollment number is defined, it must be specified either in the study population or in all cohorts.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedEnrollmentNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00133",
            RuleTemplate.ERROR,
            "Within a study design, if a planned enrollment number is defined, it must be specified either in the study population or in all cohorts.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.studyDesigns)@$sd.
    #       $sd.population@$p.
    #       $p.
    #           [
    #               (
    #                   $NullCohort:=("null" in cohorts.$type(plannedenrollmentNumber) or ($count(cohorts.plannedEnrollmentNumber)!=$count(cohorts.id))); 
    #                   $InCohort:=$boolean(cohorts.plannedEnrollmentNumber);      
    #                   $InPop:=($type(plannedEnrollmentNumber) != "null" and $exists(plannedEnrollmentNumber));  
    #                   $FValU:=function($n)
    #                       {
    #                           (
    #                               $exists($n)
    #                               ?   $type($n)="object"
    #                                   ?   $exists($n.value)
    #                                      ? $n.value&$n.unit.standardCode.decode
    #                                      : $n.minValue.value&$n.minValue.unit.standardCode.decode&" to "&
    #                                        $n.maxValue.value&$n.maxValue.unit.standardCode.decode
    #                                   : $string($n)
    #                               : "Missing"
    #                           )              
    #                       };
    #                       {
    #                           "instanceType": $p.instanceType,
    #                           "id": $p.id,
    #                           "path": $p._path,
    #                           "StudyDesign.id": $sd.id,
    #                           "StudyDesign.name": $sd.name,
    #                           "name": $p.name,
    #                           "plannedEnrollmentNumber.id": $p.plannedEnrollmentNumber.id,
    #                           "plannedEnrollmentNumber(value/range)": $FValU($p.plannedEnrollmentNumber),
    #                           "cohorts.name": "["& $join($p.cohorts.(id & ": " & name),", ") & "]",
    #                           "cohorts.plannedEnrollmentNumber.id": "["& $join($p.cohorts.(id & ": " & plannedEnrollmentNumber.id),", ") & "]",
    #                           "cohorts.plannedEnrollmentNumber(value/range)": "["& $join($p.cohorts.(id & ": " & $FValU(plannedEnrollmentNumber)),", ") & "]",
    #                           "check": (($InPop=true and $InCohort=true) or ($InPop=false and $NullCohort=true and $InCohort=true))
    #                           }
    #               )
    #           ]
    #           [check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00133: not yet implemented")
