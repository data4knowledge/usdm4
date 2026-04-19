# MANUAL: do not regenerate
#
# XHTML well-formedness check across the 6 classes that carry a syntax
# template `text` attribute. Same wrapper-and-parse approach as DDF00187.
import xml.etree.ElementTree as ET

from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = [
    "EligibilityCriterionItem",
    "Characteristic",
    "Condition",
    "Objective",
    "Endpoint",
    "IntercurrentEvent",
]

WRAPPER_OPEN = '<root xmlns="http://www.w3.org/1999/xhtml" xmlns:usdm="http://example.com/usdm">'
WRAPPER_CLOSE = "</root>"


def _is_well_formed(text: str) -> bool:
    try:
        ET.fromstring(WRAPPER_OPEN + text + WRAPPER_CLOSE)
        return True
    except ET.ParseError:
        return False


class RuleDDF00247(RuleTemplate):
    """
    DDF00247: Syntax template text is expected to be HTML formatted.

    Applies to: EligibilityCriterionItem, Characteristic, Condition, Objective, Endpoint, IntercurrentEvent
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00247",
            RuleTemplate.WARNING,
            "Syntax template text is expected to be HTML formatted.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                text = instance.get("text")
                if not isinstance(text, str) or text.strip() == "":
                    continue
                if not _is_well_formed(text):
                    self._add_failure(
                        f"{klass}.text is not well-formed XHTML",
                        klass,
                        "text",
                        data.path_by_id(instance["id"]),
                    )
        return self._result()
