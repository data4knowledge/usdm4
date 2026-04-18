from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00206(RuleTemplate):
    """
    DDF00206: Sourcing must not be defined for an administrable product which is only referenced as an embedded product for a medical device.

    Applies to: AdministrableProduct
    Attributes: sourcing
    """

    def __init__(self):
        super().__init__(
            "DDF00206",
            RuleTemplate.ERROR,
            "Sourcing must not be defined for an administrable product which is only referenced as an embedded product for a medical device.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions)@$sv.
    #       $sv.administrableProducts@$ap.
    #           [($a:=$sv.administrableProducts[id in $distinct($sv.studyInterventions.administrations.administrableProductId)].id;
    #             $p:=$sv.administrableProducts[id in $distinct($sv.medicalDevices.embeddedProductId)].id;
    #                    $ap.{
    #                       "instanceType": instanceType,
    #                       "id": id,
    #                       "path": _path,
    #                       "name": name,
    #                       "sourcing": sourcing.(decode & " (" &code&")"),
    #                       "MedicalDevice.id": $sv.medicalDevices[embeddedProductId=$ap.id]? "["&$join($sv.medicalDevices[embeddedProductId=$ap.id].id,", ")&"]",
    #                       "MedicalDevice.name": $sv.medicalDevices[embeddedProductId=$ap.id]? "["&$join($sv.medicalDevices[embeddedProductId=$ap.id].name,", ")&"]",
    #                       "MedicalDevice.embeddedProductId": $sv.medicalDevices[embeddedProductId=$ap.id]? "["&$join($sv.medicalDevices[embeddedProductId=$ap.id].embeddedProductId,", ")&"]",
    #                       "check": (id in $p)=true and (id in $a) =false and sourcing
    #                   }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00206: not yet implemented")
