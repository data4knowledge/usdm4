from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00132(RuleTemplate):
    """
    DDF00132: Within a study design, if a planned completion number is defined, it must be specified either in the study population or in all cohorts.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedCompletionNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00132",
            RuleTemplate.ERROR,
            "Within a study design, if a planned completion number is defined, it must be specified either in the study population or in all cohorts.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.studyDesigns)@$sd.
    #       $sd.population@$p.
    #       $p.
    #           [
    #               (
    #                   $NullCohort:=("null" in cohorts.$type(plannedCompletionNumber) or ($count(cohorts.plannedCompletionNumber)!=$count(cohorts.id))); 
    #                   $InCohort:=$boolean(cohorts.plannedCompletionNumber);      
    #                   $InPop:=($type(plannedCompletionNumber) != "null" and $exists(plannedCompletionNumber));  
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
    #                           "plannedCompletionNumber.id": $p.plannedCompletionNumber.id,
    #                           "plannedCompletionNumber(value/range)": $FValU($p.plannedCompletionNumber),
    #                           "cohorts.name": "["& $join($p.cohorts.(id & ": " & name),", ") & "]",
    #                           "cohorts.plannedCompletionNumber.id": "["& $join($p.cohorts.(id & ": " & plannedCompletionNumber.id),", ") & "]",
    #                           "cohorts.plannedCompletionNumber(value/range)": "["& $join($p.cohorts.(id & ": " & $FValU(plannedCompletionNumber)),", ") & "]",
    #                           "check": (($InPop=true and $InCohort=true) or ($InPop=false and $NullCohort=true and $InCohort=true))
    #                           }
    #               )
    #           ]
    #           [check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00132: not yet implemented")
