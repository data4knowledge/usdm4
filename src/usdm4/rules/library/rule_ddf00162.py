# MANUAL: do not regenerate
#
# Format check on every <usdm:ref> tag in NCItem.text. Per the rule:
# starts with "<usdm:ref", ends with "/>" or "></usdm:ref>", contains
# klass="KlassName" (letters only), id="idValue" (word chars), and
# attribute="attributeName" (letters only) in any order.
#
# Strategy: scan for any literal "<usdm:ref" occurrence. For each, try
# to match a well-formed opening + attrs + close, with all three
# required attributes present and values matching their character
# classes. A match that fails any of these checks is a malformed
# reference.
import re

from usdm4.rules.rule_template import RuleTemplate


# Finds every <usdm:ref ...> or <usdm:ref .../> — brace over any
# opening tag, good or bad.
ANY_REF_RE = re.compile(r"<usdm:ref\b([^>]*)(/?>)")

# Strict per-attribute regex (value charset enforced).
STRICT_ATTRS = {
    "klass": re.compile(r'\bklass="([A-Za-z]+)"'),
    "id": re.compile(r'\bid="(\w+)"'),
    "attribute": re.compile(r'\battribute="([A-Za-z]+)"'),
}


def _find_malformed(text: str):
    """Yield (match_text, reason) for each non-conformant <usdm:ref>."""
    idx = 0
    while True:
        start = text.find("<usdm:ref", idx)
        if start < 0:
            return
        # Advance past this occurrence for the next loop.
        idx = start + len("<usdm:ref")
        # Find the closing `>` that completes the opening tag.
        end = text.find(">", idx)
        if end < 0:
            yield text[start : start + 40], "opening tag not closed with '>'"
            return
        opener = text[start : end + 1]
        # body_between = text[start : end + 1] # Not used
        # Must end with either "/>" or have a closing "</usdm:ref>" right after.
        self_closing = opener.endswith("/>")
        paired_closing = text.startswith("</usdm:ref>", end + 1)
        if not (self_closing or paired_closing):
            yield opener, "does not end with '/>' or '></usdm:ref>'"
            continue
        # Extract the inner attribute text.
        inner = opener[len("<usdm:ref") : -2 if self_closing else -1].strip()
        missing = [
            name for name, regex in STRICT_ATTRS.items() if not regex.search(inner)
        ]
        if missing:
            yield opener, f"missing or malformed attribute(s): {', '.join(missing)}"


class RuleDDF00162(RuleTemplate):
    """
    DDF00162: When included in text, references to items stored elsewhere in the data model must be specified in the correct format.

    Applies to: NarrativeContentItem
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00162",
            RuleTemplate.ERROR,
            "When included in text, references to items stored elsewhere in the data model must be specified in the correct format. They must start with '<usdm:ref', end with either '/>' or '></usdm:ref>', and must contain 'klass=\"KlassName\"',  'id=\"idValue\"', and 'attribute=\"attributeName\"/>' in any order (where \"KlassName\" and \"attributeName\" contain only letters in upper or lower case).",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for nci in data.instances_by_klass("NarrativeContentItem"):
            text = nci.get("text")
            if not isinstance(text, str) or "<usdm:ref" not in text:
                continue
            for tag, reason in _find_malformed(text):
                self._add_failure(
                    f"Malformed <usdm:ref>: {reason} — {tag[:80]}",
                    "NarrativeContentItem",
                    "text",
                    data.path_by_id(nci["id"]),
                )
        return self._result()
