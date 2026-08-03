# MANUAL: do not regenerate
#
# The V4 version of the "at least one attribute specified for an Address"
# rule (DDF00045 is the V3 twin). Previous implementation iterated
# `LegalAddress` — a class that doesn't exist in the V4 API model (the
# only address class is `Address`) — so the loop never ran and CORE's
# legitimate finding ("All attributes of the address are blank") slipped
# past d4k.
#
# Per usdm4.api.address.Address the carried data attributes are:
#   text, lines, city, district, state, postalCode, country
from usdm4.rules.rule_template import RuleTemplate


ADDRESS_ATTRS = [
    "text",
    "lines",
    "city",
    "district",
    "state",
    "postalCode",
    "country",
]


def _any_attribute_specified(address: dict) -> bool:
    for attr in ADDRESS_ATTRS:
        value = address.get(attr)
        if value is None:
            continue
        if isinstance(value, (str, list, dict)):
            if value:
                return True
            continue
        return True
    return False


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
        for address in data.instances_by_klass("Address"):
            if not _any_attribute_specified(address):
                self._add_failure(
                    "All address attributes are blank; at least one of "
                    + ", ".join(ADDRESS_ATTRS)
                    + " must be specified",
                    "Address",
                    ", ".join(ADDRESS_ATTRS),
                    data.path_by_id(address["id"]),
                )
        return self._result()
