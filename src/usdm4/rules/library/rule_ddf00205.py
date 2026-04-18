# MANUAL: do not regenerate
#
# For each Administration: if it names both an `administrableProductId`
# AND a `medicalDeviceId`, the referenced MedicalDevice's
# `embeddedProductId` must NOT equal the Administration's
# administrableProductId. Otherwise the AP is being used as both the
# direct administrable product and the embedded product on the device —
# which the rule explicitly forbids.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00205(RuleTemplate):
    """
    DDF00205: An administrable product must not be referenced as both the administrable product for an administration and the embedded product of a medical device that is referenced by the same administration.

    Applies to: Administration
    Attributes: administrableProductId, medicalDeviceId
    """

    def __init__(self):
        super().__init__(
            "DDF00205",
            RuleTemplate.ERROR,
            "An administrable product must not be referenced as both the administrable product for an administration and the embedded product of a medical device that is referenced by the same administration.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for admin in data.instances_by_klass("Administration"):
            ap_id = admin.get("administrableProductId")
            md_id = admin.get("medicalDeviceId")
            if not (ap_id and md_id):
                continue
            device = data.instance_by_id(md_id)
            if not isinstance(device, dict):
                continue
            if device.get("embeddedProductId") == ap_id:
                self._add_failure(
                    f"Administration references AdministrableProduct {ap_id!r} directly AND as the embedded product of MedicalDevice {md_id!r}",
                    "Administration",
                    "administrableProductId, medicalDeviceId",
                    data.path_by_id(admin["id"]),
                )
        return self._result()
