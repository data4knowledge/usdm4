from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00241(RuleTemplate):
    """
    DDF00241: If the unit is the same (or missing) for both the minimum and maximum value, then the minimum value must be less than the maximum value.

    Applies to: Range
    Attributes: minValue, maxValue
    """

    def __init__(self):
        super().__init__(
            "DDF00241",
            RuleTemplate.ERROR,
            "If the unit is the same (or missing) for both the minimum and maximum value, then the minimum value must be less than the maximum value.",
        )

    # TODO: implement. MED_TEXT predicate='conditional': no template — typically a rule-specific conditional. Hand-author using the JSONata reference below.
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.**[instanceType="Range"])@$rg.
    #       $rg.
    #           [($ValU:=function($v){$v.value&($v.unit? " " & $v.unit.standardCode.decode & " ("&$v.unit.standardCode.code&")": " (unit not specified)")};
    #            $EqUnit:=(minValue.unit.standardCode.code=maxValue.unit.standardCode.code) or ((minValue.unit=null or $exists(minValue.unit)=false) and (maxValue.unit=null or $exists(maxValue.unit)=false));
    #               
    #               {
    #                   "instanceType": instanceType,
    #                   "id": id,
    #                   "path": _path,
    #                   "minValue": $ValU(minValue) ,
    #                   "maxValue": $ValU(maxValue) ,
    #                   "check": $EqUnit and (maxValue.value <= minValue.value)
    #               }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00241: not yet implemented")
