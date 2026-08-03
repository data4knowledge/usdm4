# MANUAL: do not regenerate
#
# Biconditional at the Administration level:
#   has_dose          ↔   has_admin_product (direct or embedded)
# where has_admin_product =
#   administrableProductId is set
#   OR  medicalDeviceId points to a MedicalDevice whose
#       embeddedProductId is set
# Iterate StudyVersion so medicalDevices lookup stays local.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00185(RuleTemplate):
    """
    DDF00185: If a dose is specified, then a corresponding administrable product must also be specified either directly or embedded in the medical device and vice versa.

    Applies to: Administration
    Attributes: dose, administrableProductId, medicalDeviceId
    """

    def __init__(self):
        super().__init__(
            "DDF00185",
            RuleTemplate.ERROR,
            "If a dose is specified, then a corresponding administrable product must also be specified either directly or embedded in the medical device and vice versa.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            device_embedded = {
                d.get("id"): d.get("embeddedProductId")
                for d in sv.get("medicalDevices") or []
                if isinstance(d, dict)
            }
            for intervention in sv.get("studyInterventions") or []:
                if not isinstance(intervention, dict):
                    continue
                for admin in intervention.get("administrations") or []:
                    if not isinstance(admin, dict):
                        continue
                    has_dose = bool(admin.get("dose"))
                    ap_id = admin.get("administrableProductId")
                    md_id = admin.get("medicalDeviceId")
                    embedded_ap_id = device_embedded.get(md_id) if md_id else None
                    has_product = bool(ap_id or embedded_ap_id)
                    if has_dose != has_product:
                        direction = (
                            "dose specified but no administrable product (direct or embedded)"
                            if has_dose
                            else "administrable product specified but no dose"
                        )
                        self._add_failure(
                            f"Administration: {direction}",
                            "Administration",
                            "dose, administrableProductId, medicalDeviceId",
                            data.path_by_id(admin["id"]),
                        )
        return self._result()
