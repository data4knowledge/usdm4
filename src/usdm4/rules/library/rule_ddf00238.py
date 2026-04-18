from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00238(RuleTemplate):
    """
    DDF00238: If a strength numerator quantity is specified, it must have a unit.

    Applies to: Strength
    Attributes: numerator
    """

    def __init__(self):
        super().__init__(
            "DDF00238",
            RuleTemplate.ERROR,
            "If a strength numerator quantity is specified, it must have a unit.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions)@$sv.
    #       $sv.administrableProducts@$ap.
    #       $ap.ingredients@$in.
    #       $in.substance@$su.
    #       $su.strengths@$st.
    #       $st.[(
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
    #                   "numerator.value": numerator.value,
    #                   "check": numerator.value and ($not(numerator.unit) or $exists(numerator.unit)=false)
    #               }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00238: not yet implemented")
