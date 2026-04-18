from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00194(RuleTemplate):
    """
    DDF00194: At least one attribute must be specified for an address.

    Applies to: Address
    Attributes: All
    """

    def __init__(self):
        super().__init__(
            "DDF00194",
            RuleTemplate.ERROR,
            "At least one attribute must be specified for an address.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        required_any = ['text', 'lines', 'city', 'district', 'state', 'postalCode', 'country']
        for item in data.instances_by_klass("LegalAddress"):
            if not any(item.get(a) for a in required_any):
                self._add_failure(
                    "No attributes specified; at least one required",
                    "LegalAddress",
                    ", ".join(required_any),
                    data.path_by_id(item["id"]),
                )
        return self._result()
