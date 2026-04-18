from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00211(RuleTemplate):
    """
    DDF00211: A product organization role is expected to apply to at least one medical device or administrable product.

    Applies to: ProductOrganizationRole
    Attributes: appliesTo
    """

    def __init__(self):
        super().__init__(
            "DDF00211",
            RuleTemplate.WARNING,
            "A product organization role is expected to apply to at least one medical device or administrable product.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions)@$sv.
    #       $sv.productOrganizationRoles@$pr.
    #           [($a:=$sv.administrableProducts.id;
    #             $d:=$sv.medicalDevices.id;
    #                    $pr.{
    #                       "instanceType": instanceType,
    #                       "id": id,
    #                       "path": _path,
    #                       "name": name,
    #                       "appliesToIds": appliesToIds ? "[" & $join(appliesToIds,", ")&"]",
    #                       "check": $not(appliesToIds and $map(appliesToIds,function($v){($v in $a) or ($v in $d)}))
    #                   }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00211: not yet implemented")
