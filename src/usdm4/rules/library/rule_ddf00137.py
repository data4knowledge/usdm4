# MANUAL: do not regenerate
#
# Format check on ParameterMap.reference — same shape check as
# DDF00162 but different source attribute. ParameterMap.reference is
# a single string field (not multiple tags embedded in prose), but
# the rule text is identical about what a well-formed <usdm:ref>
# looks like. Only flags when the string contains "<usdm:ref" at
# all — bare fixed-value references like "5 mg" are accepted per
# the rule's "a fixed value or a reference to items" wording.
import re

from usdm4.rules.rule_template import RuleTemplate


# Same regex machinery as DDF00162.
ANY_REF_RE = re.compile(r"<usdm:ref\b([^>]*)(/?>)")
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
        idx = start + len("<usdm:ref")
        end = text.find(">", idx)
        if end < 0:
            yield text[start:start + 40], "opening tag not closed with '>'"
            return
        opener = text[start:end + 1]
        self_closing = opener.endswith("/>")
        paired_closing = text.startswith("</usdm:ref>", end + 1)
        if not (self_closing or paired_closing):
            yield opener, "does not end with '/>' or '></usdm:ref>'"
            continue
        inner = opener[len("<usdm:ref"):-2 if self_closing else -1].strip()
        missing = [name for name, regex in STRICT_ATTRS.items() if not regex.search(inner)]
        if missing:
            yield opener, f"missing or malformed attribute(s): {', '.join(missing)}"


class RuleDDF00137(RuleTemplate):
    """
    DDF00137: References must be a fixed value or a reference to items stored elsewhere in the data model which must be specified in the correct format.

    Applies to: ParameterMap
    Attributes: reference
    """

    def __init__(self):
        super().__init__(
            "DDF00137",
            RuleTemplate.ERROR,
            "References must be a fixed value or a reference to items stored elsewhere in the data model which must be specified in the correct format. They must start with '<usdm:ref', end with either '/>' or '></usdm:ref>', and must contain 'klass=\"klassName\"', 'id=\"idValue\"', and 'attribute=\"attributeName\"/>' in any order (where \"klassName\" and \"attributeName\" contain only letters in upper or lower case).",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for pm in data.instances_by_klass("ParameterMap"):
            reference = pm.get("reference")
            if not isinstance(reference, str) or "<usdm:ref" not in reference:
                continue
            for tag, reason in _find_malformed(reference):
                self._add_failure(
                    f"Malformed <usdm:ref>: {reason} — {tag[:80]}",
                    "ParameterMap",
                    "reference",
                    data.path_by_id(pm["id"]),
                )
        return self._result()
