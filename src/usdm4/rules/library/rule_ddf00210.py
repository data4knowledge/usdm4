# MANUAL: do not regenerate
#
# YAML's class=StudyIntervention is a stage-1 extraction bug — the
# rule is actually about AdministrableProduct.productDesignation
# (see lessons_learned.md §7). ct_config.yaml already binds
# AdministrableProduct.productDesignation → C207418, so a direct
# _ct_check against the correct class is sufficient.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00210(RuleTemplate):
    """
    DDF00210: An administrable product's product designation must be specified using the product designation (C207418) DDF codelist.

    Applies to: AdministrableProduct (YAML listed StudyIntervention in error)
    Attributes: productDesignation
    """

    def __init__(self):
        super().__init__(
            "DDF00210",
            RuleTemplate.ERROR,
            "An administrable product's product designation must be specified using the product designation (C207418) DDF codelist.",
        )

    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "AdministrableProduct", "productDesignation")
