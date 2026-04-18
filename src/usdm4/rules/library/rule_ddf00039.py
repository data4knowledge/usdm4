from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00039(RuleTemplate):
    """
    DDF00039: If the duration will vary, a quantity is not expected for the duration and vice versa.

    Applies to: Duration
    Attributes: quantity
    """

    def __init__(self):
        super().__init__(
            "DDF00039",
            RuleTemplate.WARNING,
            "If the duration will vary, a quantity is not expected for the duration and vice versa.",
        )

    # TODO: implement. MED_TEXT predicate='conditional': no template — typically a rule-specific conditional. Hand-author using the JSONata reference below.
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**[instanceType="Duration"])@$d.
    #       $d.[(
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
    #                                           : $string($n)
    #                                   : $string($n)
    #                               : "Missing"
    #                       )              
    #                   };{
    #                               "instanceType": instanceType,
    #                               "id": id,
    #                               "path": _path,
    #                               "quantity(value/range)": $FValU(quantity),
    #                               "durationWillVary": durationWillVary,
    #                               "check": (durationWillVary and quantity) or (durationWillVary=false and ($not(quantity) or $exists(quantity)=false))
    #                               })][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00039: not yet implemented")
