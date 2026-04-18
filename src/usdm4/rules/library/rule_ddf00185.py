from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00185(RuleTemplate):
    """
    DDF00185: If a dose is specified, then a corresponding administrable product must also be specified either directly or embedded in the medical device and vice versa.

    Applies to: Administration
    Attributes: dose, administrableProduct
    """

    def __init__(self):
        super().__init__(
            "DDF00185",
            RuleTemplate.ERROR,
            "If a dose is specified, then a corresponding administrable product must also be specified either directly or embedded in the medical device and vice versa.",
        )

    # TODO: implement. MED_TEXT predicate='conditional': no template — typically a rule-specific conditional. Hand-author using the JSONata reference below.
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions)@$sv.
    #       $sv.studyInterventions@$si.
    #       $si.administrations@$sa.
    #           [(
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
    #                                           : "Missing"
    #                                   : $string($n)
    #                               : "Missing"
    #                       )              
    #                   };
    #               $MedProduct:=(($exists($sa.administrableProductId) and $sa.administrableProductId!=null) or ($exists($sv.medicalDevices[id=$sa.medicalDeviceId].embeddedProductId ) and $sv.medicalDevices[id=$sa.medicalDeviceId].embeddedProductId !=null));
    #                   {
    #                       "instanceType": $sa.instanceType,
    #                       "id": $sa.id,
    #                       "path": $sa._path,
    #                       "StudyIntervention.id": $si.id,
    #                       "StudyIntervention.name": $si.name,
    #                       "name": $sa.name,
    #                       "dose.id": $sa.dose.id,
    #                       "dose(value/range)": $FValU($sa.dose),
    #                       "administrableProductId": $sa.administrableProductId,
    #                       "medicalDeviceId": $sa.medicalDeviceId,
    #                       "MedicalDevice.name": $sv.medicalDevices[id=$sa.medicalDeviceId].name,
    #                       "MedicalDevice.embeddedProductId": $sv.medicalDevices[id=$sa.medicalDeviceId].embeddedProductId ,
    #                       "AdministrableProduct.name": $sv.administrableProducts[id in $append($sa.administrableProductId, $sv.medicalDevices[id=$sa.medicalDeviceId].embeddedProductId)].name,
    #                       "check": ($exists($sa.dose.id) != $MedProduct)
    #                   }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00185: not yet implemented")
