from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00186(RuleTemplate):
    """
    DDF00186: If a strength denominator is specified, it must have a unit.

    Applies to: Strength
    Attributes: denominator
    """

    def __init__(self):
        super().__init__(
            "DDF00186",
            RuleTemplate.ERROR,
            "If a strength denominator is specified, it must have a unit.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions.administrableProducts)@$ap.
    #       $ap.ingredients@$in.
    #       $in.substance@$su.
    #       $su.**.strengths@$st.
    #       $st.
    #           [(
    #                   {
    #                       "instanceType": $st.instanceType,
    #                       "id": $st.id,
    #                       "path": $st._path,
    #                       "Ingredient.id": $in.id,
    #                       "Substance.id": $su.id,
    #                       "Substance.name": $su.name,
    #                       "name": $st.name,
    #                       "denominator.id": $st.denominator.id,
    #                       "denominator.value": $st.denominator.value,
    #                       "check": $exists($st.denominator.id) and ($exists($st.denominator.unit)=false or $st.denominator.unit=null)
    #                   }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00186: not yet implemented")
