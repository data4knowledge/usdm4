from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00235(RuleTemplate):
    """
    DDF00235: A unit must not be specified for a planned completion number.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedCompletionNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00235",
            RuleTemplate.ERROR,
            "A unit must not be specified for a planned completion number.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**.studyDesigns)@$sd.
    #       $sd.population@$p.
    #      	$p.
    #      	    [
    #      	        (
    #                   $InCohortQ:=$boolean(cohorts.plannedCompletionNumber.unit);      
    #      	            $InCohortR:=($boolean(cohorts.plannedCompletionNumber.minValue.unit) or $boolean(cohorts.plannedCompletionNumber.maxValue.unit));
    #                   $InPopQ:=$boolean(plannedCompletionNumber.unit);      
    #      	            $InPopR:=($boolean(plannedCompletionNumber.minValue.unit) or $boolean(plannedCompletionNumber.maxValue.unit));
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
    #      	                    "plannedCompletionNumber.id": $p.plannedCompletionNumber.id,
    #                           "plannedCompletionNumber(value/range)": $FValU($p.plannedCompletionNumber),
    #                           "cohorts.name": "["& $join($p.cohorts.(id & ": " & name),", ") & "]",
    #                           "cohorts.plannedCompletionNumber.id": "["& $join($p.cohorts.(id & ": " & plannedCompletionNumber.id),", ") & "]",
    #     	                    "cohorts.plannedCompletionNumber(value/range)": "["& $join($p.cohorts.(id & ": " & $FValU(plannedCompletionNumber)),", ") & "]",
    #                           "check": ($InCohortQ=true or $InCohortR or $InPopQ=true or $InPopR=true)
    #                       }
    #      	        )
    #      	    ]
    #      	    [check = true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00235: not yet implemented")
