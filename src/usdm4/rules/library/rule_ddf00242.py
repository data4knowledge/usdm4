from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00242(RuleTemplate):
    """
    DDF00242: For each range, a unit must be specified either for both the minimum and the maximum value, or for neither of them.

    Applies to: Range
    Attributes: minValue, maxValue
    """

    def __init__(self):
        super().__init__(
            "DDF00242",
            RuleTemplate.ERROR,
            "For each range, a unit must be specified either for both the minimum and the maximum value, or for neither of them.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.**[instanceType="Range"])@$rg.
    #       $rg.
    #           [($ValU:=function($v){$v.value&($v.unit? " " & $v.unit.standardCode.decode & " ("&$v.unit.standardCode.code&")": " (unit not specified)")};
    #               {
    #                   "instanceType": instanceType,
    #                   "id": id,
    #                   "path": _path,
    #                   "minValue": $ValU(minValue) ,
    #                   "maxValue": $ValU(maxValue) ,
    #                   "check": $exists(minValue.unit.id) != $exists(maxValue.unit.id)
    #               }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00242: not yet implemented")
