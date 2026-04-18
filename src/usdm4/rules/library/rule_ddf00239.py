from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00239(RuleTemplate):
    """
    DDF00239: If a strength numerator range is specified, both the minValue and maxValue must have a unit.

    Applies to: Strength
    Attributes: numerator
    """

    def __init__(self):
        super().__init__(
            "DDF00239",
            RuleTemplate.ERROR,
            "If a strength numerator range is specified, both the minValue and maxValue must have a unit.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions)@$sv.
    #       $sv.administrableProducts@$ap.
    #       $ap.ingredients@$in.
    #       $in.substance@$su.
    #       $su.**.strengths@$st.
    #       $st.[($ValU:=function($v){$v.value&($v.unit? " " & $v.unit.standardCode.decode & " ("&$v.unit.standardCode.code&")": " (unit not specified)")};
    #               {
    #                   "instanceType": instanceType,
    #                   "id": id,
    #                   "path": _path,
    #                   "AdministrableProduct.id": $ap.id,
    #                   "AdministrableProduct.name": $ap.name,
    #                   "Ingredient.id": $in.id,
    #                   "Substance.id": $su.id,
    #                   "Substance.name": $su.name,
    #                   "name": name,
    #                   "numerator.minValue": $ValU(numerator.minValue) ,
    #                   "numerator.maxValue": $ValU(numerator.maxValue) ,
    #                   "check": (numerator.minValue.value and ($not(numerator.minValue.unit) or $exists(numerator.minValue.unit)=false)) or (numerator.maxValue.value and ($not(numerator.maxValue.unit) or $exists(numerator.maxValue.unit)=false))
    #               }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00239: not yet implemented")
