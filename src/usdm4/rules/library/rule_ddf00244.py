# MANUAL: do not regenerate
#
# Same <usdm:ref> validation as DDF00124 but against
# NarrativeContentItem.text. Shared helpers live inline to avoid pulling
# in a new module for two callers; if a third rule needs this, promote
# to a tiny utility.
import re

from usdm4.rules.rule_template import RuleTemplate


USDM_REF_RE = re.compile(r"<usdm:ref\b([^>]*)(?:/>|>\s*</usdm:ref>)")
ATTR_RE = {
    "klass": re.compile(r'klass="([a-zA-Z]+)"'),
    "id": re.compile(r'id="([\w-]+)"'),
    "attribute": re.compile(r'attribute="([a-zA-Z]+)"'),
}


def _parse_ref(raw_attrs):
    out = {}
    for name, regex in ATTR_RE.items():
        m = regex.search(raw_attrs)
        if m:
            out[name] = m.group(1)
    return out


def _check_ref(data, ref):
    if not {"klass", "id", "attribute"}.issubset(ref):
        return "ref is missing klass / id / attribute"
    target = data.instance_by_id(ref["id"])
    if not isinstance(target, dict):
        return f"id {ref['id']!r} does not resolve to an instance"
    if target.get("instanceType") != ref["klass"]:
        return f"id {ref['id']!r} resolves to {target.get('instanceType')} (expected {ref['klass']})"
    if ref["attribute"] not in target:
        return f"attribute {ref['attribute']!r} not present on {ref['klass']} {ref['id']!r}"
    return None


class RuleDDF00244(RuleTemplate):
    """
    DDF00244: Referenced items in the narrative content item texts must be available elsewhere in the data model.

    Applies to: NarrativeContentItem
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00244",
            RuleTemplate.ERROR,
            "Referenced items in the narrative content item texts must be available elsewhere in the data model.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for nci in data.instances_by_klass("NarrativeContentItem"):
            text = nci.get("text")
            if not isinstance(text, str) or "usdm:ref" not in text:
                continue
            for match in USDM_REF_RE.finditer(text):
                ref = _parse_ref(match.group(1))
                problem = _check_ref(data, ref)
                if problem:
                    self._add_failure(
                        f"NarrativeContentItem reference problem: {problem}",
                        "NarrativeContentItem",
                        "text",
                        data.path_by_id(nci["id"]),
                    )
        return self._result()
