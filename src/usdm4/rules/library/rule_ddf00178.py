from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00178(RuleTemplate):
    """
    DDF00178: If a dose is specified then a corresponding frequency must also be specified.

    Applies to: Administration
    Attributes: dose
    """

    def __init__(self):
        super().__init__(
            "DDF00178",
            RuleTemplate.ERROR,
            "If a dose is specified then a corresponding frequency must also be specified.",
        )

    # TODO: implement. MED_TEXT predicate='conditional': no template — typically a rule-specific conditional. Hand-author using the JSONata reference below.
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions.studyInterventions)@$si.
    #       $si.administrations@$sa.
    #           [(
    #               $ValU:=function($v){$v.value&($v.unit? " " & $v.unit.standardCode.decode & " ("&$v.unit.standardCode.code&")")};
    #               $FValU:=function($n)
    #                   {
    #                       (
    #                           $exists($n)
    #                               ?   $type($n)="object"
    #                                   ?   $exists($n.value)
    #                                       ? $ValU($n)
    #                                       : $exists($n.minValue) or $exists($n.maxValue)
    #                                           ? $ValU($n.minValue)&" to "&$ValU($n.maxValue)
    #                                           : "Missing"
    #                                   : $string($n)
    #                               : "Missing"
    #                       )              
    #                   };
    #                   {
    #                       "instanceType": $sa.instanceType,
    #                       "id": $sa.id,
    #                       "path": $sa._path,
    #                       "StudyIntervention.id": $si.id,
    #                       "StudyIntervention.name": $si.name,
    #                       "name": $sa.name,
    #                       "dose.id": $sa.dose.id,
    #                       "dose(value/range)": $FValU($sa.dose),
    #                       "frequency.id": $sa.frequency.id,
    #                      "frequency": ($sa.frequency ? ($sa.frequency.standardCode.decode & " (" & $sa.frequency.standardCode.code & ")")),
    #                      "check": ($exists($sa.dose.id) and $exists($sa.frequency.id)=false)
    #                   }
    #           )][check=true]    

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00178: not yet implemented")
