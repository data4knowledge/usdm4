# MANUAL: do not regenerate
#
# "HTML formatted" interpreted as well-formed XHTML: text wrapped in a
# namespace-declaring root must parse. Empty/None is accepted (absence
# is covered by other rules). `<usdm:ref>` tags in text require the
# `usdm` namespace prefix to be declared on the wrapper so parsing
# doesn't trip on undeclared prefixes.
import xml.etree.ElementTree as ET

from usdm4.rules.rule_template import RuleTemplate


WRAPPER_OPEN = '<root xmlns="http://www.w3.org/1999/xhtml" xmlns:usdm="http://example.com/usdm">'
WRAPPER_CLOSE = "</root>"


def _is_well_formed(text: str) -> bool:
    try:
        ET.fromstring(WRAPPER_OPEN + text + WRAPPER_CLOSE)
        return True
    except ET.ParseError:
        return False


class RuleDDF00187(RuleTemplate):
    """
    DDF00187: Narrative content item text is expected to be HTML formatted.

    Applies to: NarrativeContentItem
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00187",
            RuleTemplate.WARNING,
            "Narrative content item text is expected to be HTML formatted.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for nci in data.instances_by_klass("NarrativeContentItem"):
            text = nci.get("text")
            if not isinstance(text, str) or text.strip() == "":
                continue
            if not _is_well_formed(text):
                self._add_failure(
                    "NarrativeContentItem.text is not well-formed XHTML",
                    "NarrativeContentItem",
                    "text",
                    data.path_by_id(nci["id"]),
                )
        return self._result()
