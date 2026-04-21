# MANUAL: do not regenerate
#
# Every id in ProductOrganizationRole.appliesToIds must resolve to an
# AdministrableProduct or a MedicalDevice instance. Unresolved ids or
# ids pointing to the wrong class are failures.
from usdm4.rules.rule_template import RuleTemplate


ALLOWED_CLASSES = {"AdministrableProduct", "MedicalDevice"}


class RuleDDF00212(RuleTemplate):
    """
    DDF00212: If 'appliesTo' is specified for a product organization role, then the product organization role must only apply to medical devices or administrable products.

    Applies to: ProductOrganizationRole
    Attributes: appliesToIds
    """

    def __init__(self):
        super().__init__(
            "DDF00212",
            RuleTemplate.ERROR,
            "If 'appliesTo' is specified for a product organization role, then the product organization role must only apply to medical devices or administrable products.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for role in data.instances_by_klass("ProductOrganizationRole"):
            for target_id in role.get("appliesToIds") or []:
                if not target_id:
                    continue
                target = data.instance_by_id(target_id)
                target_type = target.get("instanceType") if isinstance(target, dict) else None
                if target_type not in ALLOWED_CLASSES:
                    reason = (
                        "does not resolve to any instance"
                        if target is None
                        else f"resolves to {target_type} (not AdministrableProduct or MedicalDevice)"
                    )
                    self._add_failure(
                        f"ProductOrganizationRole.appliesToIds entry {target_id!r} {reason}",
                        "ProductOrganizationRole",
                        "appliesToIds",
                        data.path_by_id(role["id"]),
                    )
        return self._result()
