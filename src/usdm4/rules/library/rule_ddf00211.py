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

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("ProductOrganizationRole"):
            if not item.get("appliesTo"):
                self._add_failure(
                    "Required attribute 'appliesTo' is missing or empty",
                    "ProductOrganizationRole",
                    "appliesTo",
                    data.path_by_id(item["id"]),
                )
        return self._result()
