from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00177(RuleTemplate):
    """
    DDF00177: If an administration's dose is specified then a corresponding route is expected and vice versa.

    Applies to: Administration
    Attributes: dose, route
    """

    def __init__(self):
        super().__init__(
            "DDF00177",
            RuleTemplate.WARNING,
            "If an administration's dose is specified then a corresponding route is expected and vice versa.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
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
    #                       "dose(value)": $FValU($sa.dose),
    #                       "route.id": $sa.route.id,
    #                       "route": ($sa.route? ($sa.route.standardCode.decode & " (" & $sa.route.standardCode.code & ")")),
    #                       "check": $exists($sa.dose.id) != $exists($sa.route.id)
    #                   }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00177: not yet implemented")
