from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00253(RuleTemplate):
    """
    DDF00253: A reference substance must not have a reference substance.

    Applies to: Substance
    Attributes: referenceSubstance
    """

    def __init__(self):
        super().__init__(
            "DDF00253",
            RuleTemplate.ERROR,
            "A reference substance must not have a reference substance.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions.administrableProducts)@$ap.
    #       $ap.ingredients@$in.
    #       $in.substance@$su.
    #       $su.referenceSubstance.
    #               [
    #                               {
    #                               "id": id,
    #                               "instanceType": instanceType,
    #                               "path": _path,
    #                               "AdministrableProduct.id": $ap.id,
    #                               "AdministrableProduct.name": $ap.name,
    #                               "Ingredient.id": $in.id,
    #                               "parent Substance.id": $su.id,
    #                               "parent Substance.name": $su.name,
    #                               "name": name,
    #                               "referenceSubstance.id": referenceSubstance.id,
    #                               "referenceSubstance.name": referenceSubstance.name,
    #                               "check": $not(referenceSubstance)=false
    #                               }
    #                   ][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00253: not yet implemented")
