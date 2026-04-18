from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00234(RuleTemplate):
    """
    DDF00234: A unit must not be specified for a planned enrollment number.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedEnrollmentNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00234",
            RuleTemplate.ERROR,
            "A unit must not be specified for a planned enrollment number.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.studyDesigns)@$sd.
    #       $sd.population@$p.
    #      	$p.
    #      	    [
    #      	        (
    #                   $InCohortQ:=$boolean(cohorts.plannedEnrollmentNumber.unit);      
    #      	            $InCohortR:=($boolean(cohorts.plannedEnrollmentNumber.minValue.unit) or $boolean(cohorts.plannedEnrollmentNumber.maxValue.unit));
    #                   $InPopQ:=$boolean(plannedEnrollmentNumber.unit);      
    #      	            $InPopR:=($boolean(plannedEnrollmentNumber.minValue.unit) or $boolean(plannedEnrollmentNumber.maxValue.unit));
    #                   $FValU:=function($n)
    #                       {
    #                           (
    #                               $exists($n)
    #                               ?   $type($n)="object"
    #                                   ?   $exists($n.value)
    #                                       ? $exists($n.unit.id)
    #                                           ? $n.value & " " & $n.unit.standardCode.decode & " (" & $n.unit.standardCode.code & ")" 
    #                                           : $n.value                                      
    #                                       : $exists($n.minValue)
    #                                           ? $exists($n.minValue.unit.id) or  $exists($n.maxValue.unit.id)
    #                                               ? $n.minValue.value & " " & $n.minValue.unit.standardCode.decode &  "(" & $n.minValue.unit.standardCode.code & 
    #                                                   ") to " & $n.maxValue.value & " " & $n.maxValue.unit.standardCode.decode &  "(" & $n.maxValue.unit.standardCode.code & ")"
    #                                               : $n.minValue.value & " to " & $n.maxValue.value
    #                                           : $string($n)
    #                                   : $string($n)
    #                               : "Missing"
    #                           )              
    #                       };
    #                   	{
    #      	                    "instanceType": $p.instanceType,
    #      	                    "id": $p.id,
    #      	                    "path": $p._path,
    #                           "StudyDesign.id": $sd.id,
    #      	                    "StudyDesign.name": $sd.name,
    #      	                    "name": $p.name,
    #      	                    "plannedEnrollmentNumber.id": $p.plannedEnrollmentNumber.id,
    #                           "plannedEnrollmentNumber(value/range)": $FValU($p.plannedEnrollmentNumber),
    #                           "cohorts.name": "["& $join($p.cohorts.(id & ": " & name),", ") & "]",
    #                           "cohorts.plannedEnrollmentNumber.id": "["& $join($p.cohorts.(id & ": " & plannedEnrollmentNumber.id),", ") & "]",
    #     	                    "cohorts.plannedEnrollmentNumber(value/range)": "["& $join($p.cohorts.(id & ": " & $FValU(plannedEnrollmentNumber)),", ") & "]",
    #                           "check": ($InCohortQ=true or $InCohortR or $InPopQ=true or $InPopR=true)
    #                       }
    #      	        )
    #      	    ]
    #      	    [check = true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00234: not yet implemented")
