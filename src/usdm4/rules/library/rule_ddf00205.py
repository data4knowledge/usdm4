from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00205(RuleTemplate):
    """
    DDF00205: An administrable product must not be referenced as both the administrable product for an administration and the embedded product of a medical device that is referenced by the same administration.

    Applies to: Administration
    Attributes: administrableProduct
    """

    def __init__(self):
        super().__init__(
            "DDF00205",
            RuleTemplate.ERROR,
            "An administrable product must not be referenced as both the administrable product for an administration and the embedded product of a medical device that is referenced by the same administration.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions)@$sv.
    #       $sv.studyInterventions@$si.
    #       $si.administrations@$sa.
    #           [(
    #                    {
    #                       "instanceType": $sa.instanceType,
    #                       "id": $sa.id,
    #                       "path": $sa._path,
    #                       "StudyIntervention.id": $si.id,
    #                       "StudyIntervention.name": $si.name,
    #                       "name": $sa.name,
    #                       "administrableProductId": $sa.administrableProductId,
    #                       "AdministrableProduct.name": $sv.administrableProducts[id=$sa.administrableProductId].name,
    #                       "medicalDeviceId": $sa.medicalDeviceId,
    #                       "MedicalDevice.name": $sv.medicalDevices[id=$sa.medicalDeviceId].name,
    #                       "check": ($exists($sa.medicalDeviceId) and $sv.medicalDevices[id=$sa.medicalDeviceId].embeddedProductId= $sa.administrableProductId)
    #                   }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00205: not yet implemented")
