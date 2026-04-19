# MANUAL: do not regenerate
#
# ParameterMap.reference contains <usdm:ref klass="X" id="Y"
# attribute="Z"/> markers. For each marker, the (klass, id, attribute)
# triple must resolve: instance with that id exists, its instanceType
# matches klass, and it has a non-null value at the named attribute.
# The regex is order-tolerant on klass / id / attribute.
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


class RuleDDF00124(RuleTemplate):
    """
    DDF00124: Referenced items in a parameter map must be available elsewhere in the data model.

    Applies to: ParameterMap
    Attributes: reference
    """

    def __init__(self):
        super().__init__(
            "DDF00124",
            RuleTemplate.ERROR,
            "Referenced items in a parameter map must be available elsewhere in the data model.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for pm in data.instances_by_klass("ParameterMap"):
            reference = pm.get("reference")
            if not isinstance(reference, str):
                continue
            for match in USDM_REF_RE.finditer(reference):
                ref = _parse_ref(match.group(1))
                problem = _check_ref(data, ref)
                if problem:
                    self._add_failure(
                        f"ParameterMap reference problem: {problem}",
                        "ParameterMap",
                        "reference",
                        data.path_by_id(pm["id"]),
                    )
        return self._result()
