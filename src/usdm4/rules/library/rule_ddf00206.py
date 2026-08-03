# MANUAL: do not regenerate
#
# For each StudyVersion: an AdministrableProduct is "only embedded" if
# it is referenced as `embeddedProductId` by at least one MedicalDevice
# AND is NOT referenced as `administrableProductId` by any
# Administration. "Only embedded" APs must have `sourcing` empty/absent.
from usdm4.rules.rule_template import RuleTemplate


def _is_specified(value):
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return bool(value)
    return True


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

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            embedded_ids: set = set()
            for device in sv.get("medicalDevices") or []:
                if isinstance(device, dict) and device.get("embeddedProductId"):
                    embedded_ids.add(device["embeddedProductId"])
            administered_ids: set = set()
            for intervention in sv.get("studyInterventions") or []:
                if not isinstance(intervention, dict):
                    continue
                for admin in intervention.get("administrations") or []:
                    if isinstance(admin, dict) and admin.get("administrableProductId"):
                        administered_ids.add(admin["administrableProductId"])
            for ap in sv.get("administrableProducts") or []:
                if not isinstance(ap, dict):
                    continue
                ap_id = ap.get("id")
                if ap_id not in embedded_ids or ap_id in administered_ids:
                    continue
                if _is_specified(ap.get("sourcing")):
                    self._add_failure(
                        "AdministrableProduct is only referenced as an embedded product but has sourcing defined",
                        "AdministrableProduct",
                        "sourcing",
                        data.path_by_id(ap_id),
                    )
        return self._result()
