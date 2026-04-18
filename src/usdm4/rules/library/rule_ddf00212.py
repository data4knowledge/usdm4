from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00212(RuleTemplate):
    """
    DDF00212: If 'appliesTo' is specified for a product organization role, then the product organization role must only apply to medical devices or administrable products.

    Applies to: ProductOrganizationRole
    Attributes: appliesTo
    """

    def __init__(self):
        super().__init__(
            "DDF00212",
            RuleTemplate.ERROR,
            "If 'appliesTo' is specified for a product organization role, then the product organization role must only apply to medical devices or administrable products.",
        )

    # TODO: implement. MED_TEXT predicate='conditional': no template — typically a rule-specific conditional. Hand-author using the JSONata reference below.
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions)@$sv.
    #       $sv.productOrganizationRoles@$pr.
    #           [($a:=$sv.administrableProducts.id;
    #             $d:=$sv.medicalDevices.id;
    #             $medDev:=function($i){$sv.medicalDevices[id=$i].(id? id &": "&name)};
    #             $admProd:=function($i){$sv.administrableProducts[id=$i].(id? id &": "&name)};
    #                    $pr.{
    #                       "instanceType": instanceType,
    #                       "id": id,
    #                       "path": _path,
    #                       "name": name,
    #                       "appliesToIds": appliesToIds ? "[" & $join(appliesToIds,", ")&"]",
    #                       "appliesTo name": "["&$join($map(appliesToIds,function($b){$medDev($b)?$medDev($b):($admProd($b)?$admProd($b):$b & ": Invalid reference")}),", ")&"]",
    #                       "check": false in $map(appliesToIds,function($v){($v in $a) or ($v in $d)})
    #                   }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00212: not yet implemented")
