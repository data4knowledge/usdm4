"""
JSONata → Python translator for CORE rule conditions.

This is NOT a general JSONata interpreter. It's a narrow pattern-matcher
that recognises the uniform shapes CORE uses across its 92 JSONata rules
and emits idiomatic Python leaning on usdm4.data_store.DataStore and
usdm4.rules.primitives.

Patterns handled (start small, extend):

  1. CROSS_INSTANCE_UNIQUE
     "All <instances> defined for a <scope> must be unique."
     JSONata shape:
         <scope_root>@$scope.
           $filter($scope.<collection>, function($v,$i,$a){
             $count($a[<key>=$v.<key>])>1
           }) ...

  2. INTRA_ATTRIBUTE_UNIQUE
     "A <thing> must not be referenced more than once by the same <parent>."
     JSONata shape:
         <scope_root>.
           {... "Duplicate <ids>":
             $filter(<idlist>, function($v,$i,$a){$count($a[$=$v])>1}) ...
           }[...]

Rules matching neither pattern are returned as NoMatch and fall through to
the regular review path.

Usage as a library:
    from tools.translate_jsonata import translate
    result = translate(jsonata_string, ddf_id, rule_text, attribute_hint)
    if result.success:
        result.python_body    # str, emits a validate(self, config) body

Usage as CLI (walking-skeleton debugging):
    python tools/translate_jsonata.py --only DDF00170,DDF00069
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────
# Result types
# ──────────────────────────────────────────────────────────────────────────


@dataclass
class TranslationResult:
    success: bool
    pattern: str                 # e.g. "CROSS_INSTANCE_UNIQUE", "NO_MATCH"
    python_body: str = ""        # full validate() body when success=True
    python_imports: list = None  # additional imports beyond RuleTemplate
    notes: str = ""              # human-readable commentary for the reviewer

    def __post_init__(self):
        if self.python_imports is None:
            self.python_imports = []


# ──────────────────────────────────────────────────────────────────────────
# Pattern recognisers
# ──────────────────────────────────────────────────────────────────────────

# JSONata collection-key shape:
#     <scope_root>@$<var>.
#       $filter($<var>.<collection>, function($v,$i,$a){
#         $count($a[<key>=$v.<key>])>1
#       })
# Capture: scope_var name, collection attr, key attr(s)
CROSS_INSTANCE_RE = re.compile(
    r"""
    ^\s*                                            # optional leading whitespace
    \$?([a-zA-Z_.]+)                                # scope_root e.g. "study.versions" or "study.versions.studyDesigns"
    (?:@\$(?P<scope_var>\w+))?                      # optional scope binding @$sv
    \s*\.\s*
    (?:\()?\s*                                      # optional open-paren
    \$filter\(                                      # $filter(
        \$(?P<ref_scope>\w+)\.(?P<collection>\w+)   #   $sv.abbreviations
        ,\s*function\(\$v,\$i,\$a\)\s*\{             #   , function($v,$i,$a) {
        \s*\$count\(\$a\[                           #     $count($a[
        (?P<key_predicate>[^\]]+)                   #       <predicate>
        \]\)\s*>\s*1                                #     ])>1
        \s*\}                                       #   }
    \s*\)                                           # )
    """,
    re.X | re.S,
)

# JSONata intra-attribute-dupes shape:
#     <scope_path>.
#       { "instanceType": ..., "Duplicate <thing>":
#         $filter(<idlist>, function($v,$i,$a){$count($a[$=$v])>1}) ~> $sort
#       }[`Duplicate <thing>`]
#
# We look for the filter form:
#     $filter(<idlist_attr>, function($v,$i,$a){$count($a[$=$v])>1})
INTRA_ATTR_RE = re.compile(
    r"""
    \$filter\(
        (?P<idlist>\w+)                              # documentVersionIds
        ,\s*function\(\$v,\$i,\$a\)\s*\{
        \s*\$count\(\$a\[\s*\$\s*=\s*\$v\s*\]\)\s*>\s*1
        \s*\}
    \s*\)
    """,
    re.X,
)


# ──────────────────────────────────────────────────────────────────────────
# Helpers to map JSONata scope paths to a DataStore-friendly class
# ──────────────────────────────────────────────────────────────────────────

# CORE's top-level paths map to these USDM classes (the last segment is usually
# the collection attribute of the parent; the element class is derived from
# the rule's entity/attribute context).
SCOPE_PATH_TO_CLASS = {
    "study.versions": ["StudyVersion"],
    "study.versions.studyDesigns": ["InterventionalStudyDesign", "ObservationalStudyDesign"],
    "study.documentedBy": ["StudyDefinitionDocument"],
    "study": ["Study"],
}


def scope_classes_from_path(path: str) -> Optional[list[str]]:
    """Resolve a JSONata path like 'study.versions' to USDM class name(s)."""
    # Strip leading "$." if present
    p = path.lstrip("$.").rstrip(".")
    return SCOPE_PATH_TO_CLASS.get(p)


def key_expr_to_python(predicate: str, scope_var: str) -> Optional[str]:
    """
    Convert a JSONata key predicate like "armId=$v.armId and epochId=$v.epochId"
    or "$.abbreviatedText=$v.abbreviatedText" into a Python tuple key expression.

    Returns None if the predicate is too complex for this translator.
    """
    predicate = predicate.strip()

    # Case 1: "$.<attr>=$v.<attr>" (same attribute both sides — single-key uniqueness)
    m = re.fullmatch(r"\$\.(\w+)\s*=\s*\$v\.(\w+)", predicate)
    if m and m.group(1) == m.group(2):
        attr = m.group(1)
        return f'item.get("{attr}")', [attr]

    # Case 2: "<attr>=$v.<attr> and <attr2>=$v.<attr2>" (composite key)
    m = re.fullmatch(
        r"(\w+)\s*=\s*\$v\.(\w+)\s+and\s+(\w+)\s*=\s*\$v\.(\w+)",
        predicate,
    )
    if m and m.group(1) == m.group(2) and m.group(3) == m.group(4):
        a1, a2 = m.group(1), m.group(3)
        return f'(item.get("{a1}"), item.get("{a2}"))', [a1, a2]

    return None


# ──────────────────────────────────────────────────────────────────────────
# Translators
# ──────────────────────────────────────────────────────────────────────────


def try_cross_instance_unique(
    jsonata: str, ddf_id: str, text: str, attribute_hint: str
) -> Optional[TranslationResult]:
    """
    Match the cross-instance-uniqueness pattern and emit Python.

    Returns None if the JSONata doesn't fit the pattern.
    """
    m = CROSS_INSTANCE_RE.search(jsonata)
    if not m:
        return None

    scope_root = m.group(1).rstrip(".")
    scope_classes = scope_classes_from_path(scope_root)
    if not scope_classes:
        return None

    collection = m.group("collection")
    key_result = key_expr_to_python(m.group("key_predicate"), m.group("scope_var") or "")
    if key_result is None:
        return None
    key_expr, key_attrs = key_result

    # Derive the iterated class from CORE: the element class is stored separately,
    # but for typical cases collection+"one-to-many" → class name capitalised and
    # singularised. Since naming isn't always predictable, we require it from
    # the caller via attribute_hint OR fall back to a heuristic.
    element_class = singular_capitalize(collection)

    # Compose the validate() body
    scope_list_literal = repr(scope_classes)
    # _add_failure takes (message, klass, attribute, path) — if there are
    # multiple key attrs, join them into one string for the attribute field.
    attribute_str = ", ".join(key_attrs)
    # f-string interpolation for the message: use single-quoted inner strings
    # because the outer f-string uses double quotes (Python <3.12 compat).
    if len(key_attrs) == 1:
        msg_interp = "{item.get('" + key_attrs[0] + "')!r}"
    else:
        parts = ", ".join("{item.get('" + a + "')!r}" for a in key_attrs)
        msg_interp = f"({parts})"

    body = f"""    def validate(self, config: dict) -> bool:
        data = config["data"]
        seen: dict = {{}}
        for item in data.instances_by_klass("{element_class}"):
            scope = data.parent_by_klass(item["id"], {scope_list_literal})
            if scope is None:
                continue
            key = (scope["id"], {key_expr})
            if key in seen:
                self._add_failure(
                    f"Duplicate {msg_interp} within scope",
                    "{element_class}",
                    "{attribute_str}",
                    data.path_by_id(item["id"]),
                )
            else:
                seen[key] = item["id"]
        return self._result()
"""

    return TranslationResult(
        success=True,
        pattern="CROSS_INSTANCE_UNIQUE",
        python_body=body,
        notes=f"collection={collection!r} → class={element_class!r}, scope={scope_classes}, key_attrs={key_attrs}",
    )


def singular_capitalize(name: str) -> str:
    """Heuristic: 'abbreviations' -> 'Abbreviation', 'studyCells' -> 'StudyCell'."""
    if name.endswith("ies"):
        stem = name[:-3] + "y"
    elif name.endswith("s") and not name.endswith("ss"):
        stem = name[:-1]
    else:
        stem = name
    return stem[:1].upper() + stem[1:]


def try_intra_attribute_unique(
    jsonata: str, ddf_id: str, text: str, attribute_hint: str
) -> Optional[TranslationResult]:
    """
    Match the intra-attribute-duplicates pattern.

    The element is the instance iterated at the top level; the duplicate
    check is within one of its array attributes.
    """
    m = INTRA_ATTR_RE.search(jsonata)
    if not m:
        return None
    idlist_attr = m.group("idlist")

    # Need the scope root to know which class iterates. Look for the top-level
    # path segment (e.g. "study.versions." at the start).
    first_line = jsonata.strip().split("\n")[0]
    # Grab the top-level path
    m_path = re.match(r"\$?\.?(\w[\w.]*)\s*\.", first_line)
    if not m_path:
        return None
    scope_path = m_path.group(1)
    scope_classes = scope_classes_from_path(scope_path)
    if not scope_classes:
        return None

    # Single element-class iteration
    element_class = scope_classes[0]
    body = f"""    def validate(self, config: dict) -> bool:
        from usdm4.rules.primitives import duplicate_values
        data = config["data"]
        for item in data.instances_by_klass("{element_class}"):
            dupes = duplicate_values(item.get("{idlist_attr}") or [])
            if dupes:
                self._add_failure(
                    f"Duplicate {{dupes!r}} in {idlist_attr}",
                    "{element_class}",
                    "{idlist_attr}",
                    data.path_by_id(item["id"]),
                )
        return self._result()
"""

    return TranslationResult(
        success=True,
        pattern="INTRA_ATTRIBUTE_UNIQUE",
        python_body=body,
        notes=f"element={element_class!r}, idlist={idlist_attr!r}",
    )


# ──────────────────────────────────────────────────────────────────────────
# Top-level entry
# ──────────────────────────────────────────────────────────────────────────


def try_subset_check(jsonata: str, ddf_id: str, text: str, attribute_hint: str) -> Optional[TranslationResult]:
    """
    Pattern: "X must only reference ids that resolve within the same <scope>."
    JSONata shape:
        <scope_root>@$<var>.
          [ $<var>.<collection>.<id_attr>[$not($ in $<var>.<collection>.id)]. {...} ]

    Example — DDF00254:
        $.**.studyDesigns@$s.
          [ $s.activities.childIds[$not($ in $s.activities.id)]. {...} ]
    """
    m = re.search(
        r"""
        \$?([a-zA-Z.*]+)\s*@\$(?P<var>\w+)\s*\.\s*
        \[?\s*                                       # optional open bracket
        \$(?P=var)\.(?P<coll>\w+)\.(?P<id_attr>\w+)  # $s.activities.childIds
        \[\$not\(\$\s+in\s+                          # [$not($ in
        \$(?P=var)\.(?P=coll)\.id                    # $s.activities.id
        \)\]
        """,
        jsonata,
        re.X | re.S,
    )
    if not m:
        return None
    scope_path = m.group(1).lstrip("$.*").rstrip(".")
    # $.**.studyDesigns → studyDesigns
    if "studyDesigns" in scope_path:
        scope_classes = ["InterventionalStudyDesign", "ObservationalStudyDesign"]
    else:
        scope_classes = scope_classes_from_path(scope_path)
        if not scope_classes:
            return None

    collection = m.group("coll")
    id_attr = m.group("id_attr")
    element_class = singular_capitalize(collection)
    scope_list_literal = repr(scope_classes)

    body = f"""    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("{element_class}"):
            scope = data.parent_by_klass(item["id"], {scope_list_literal})
            if scope is None:
                continue
            # Collect ids of same-class siblings within this scope
            sibling_ids = {{
                sib["id"]
                for sib in data.instances_by_klass("{element_class}")
                if (sp := data.parent_by_klass(sib["id"], {scope_list_literal})) is not None
                and sp["id"] == scope["id"]
            }}
            for ref_id in item.get("{id_attr}") or []:
                if ref_id not in sibling_ids:
                    self._add_failure(
                        f"{id_attr} references {{ref_id!r}} outside the same scope",
                        "{element_class}",
                        "{id_attr}",
                        data.path_by_id(item["id"]),
                    )
        return self._result()
"""
    return TranslationResult(
        success=True,
        pattern="SUBSET_WITHIN_SCOPE",
        python_body=body,
        notes=f"element={element_class!r}, id_attr={id_attr!r}, scope={scope_classes}",
    )


def try_incompat_codes(jsonata: str, ddf_id: str, text: str, attribute_hint: str) -> Optional[TranslationResult]:
    """
    Pattern: "<class> must not have both <code1> and <code2> in a coded list attribute."
    JSONata shape:
        <root>.<class>["<code1>" in <attr>.code and "<code2>" in <attr>.code]. {...}

    Example — DDF00154:
        study.versions.studyDesigns["C217004" in characteristics.code and "C217005" in characteristics.code]
    """
    m = re.search(
        r"""
        \$?([a-zA-Z.]+)\s*                            # scope path: study.versions.studyDesigns
        \[\s*
        "(?P<code1>C\d+)"\s+in\s+(?P<coded_attr>\w+)\.code
        \s+and\s+
        "(?P<code2>C\d+)"\s+in\s+(?P=coded_attr)\.code
        \s*\]
        """,
        jsonata,
        re.X,
    )
    if not m:
        return None
    scope_path = m.group(1).rstrip(".")
    scope_classes = scope_classes_from_path(scope_path)
    if not scope_classes:
        return None
    element_class = scope_classes[0]  # direct iteration
    coded_attr = m.group("coded_attr")
    code1, code2 = m.group("code1"), m.group("code2")

    body = f"""    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("{element_class}"):
            codes = [c.get("code") for c in (item.get("{coded_attr}") or []) if isinstance(c, dict)]
            if "{code1}" in codes and "{code2}" in codes:
                self._add_failure(
                    f"Incompatible codes {code1} and {code2} both present in {coded_attr}",
                    "{element_class}",
                    "{coded_attr}",
                    data.path_by_id(item["id"]),
                )
        return self._result()
"""
    return TranslationResult(
        success=True,
        pattern="INCOMPATIBLE_CODES",
        python_body=body,
        notes=f"element={element_class!r}, attr={coded_attr!r}, codes=({code1}, {code2})",
    )


def try_at_least_one(jsonata: str, ddf_id: str, text: str, attribute_hint: str) -> Optional[TranslationResult]:
    """
    Pattern: "at least one of a set of attributes must be specified on an instance."
    JSONata shape:
        <root>.<collection>@$<var>.
          $<var>.<nested>[$not(a or b or c or ...)]. {...}

    Example — DDF00194 (address):
        study.versions.organizations@$o.
          $o.legalAddress[$not(text or lines or city or district or state or postalCode or country)]
    """
    m = re.search(
        r"""
        \$?([a-zA-Z.]+)\s*@\$(?P<var>\w+)\s*\.\s*      # root@$o.
        \$(?P=var)\.(?P<nested>\w+)                     # $o.legalAddress
        \[\$not\(
        (?P<attrs>(?:[a-zA-Z]+\s+or\s+){2,}[a-zA-Z]+)  # text or lines or ...
        \)\]
        """,
        jsonata,
        re.X,
    )
    if not m:
        return None
    # Scope class is not used directly — we iterate the nested class.
    nested_attr = m.group("nested")
    element_class = singular_capitalize(nested_attr)
    attrs = [a.strip() for a in re.split(r"\s+or\s+", m.group("attrs"))]
    attrs_list_literal = repr(attrs)

    body = f"""    def validate(self, config: dict) -> bool:
        data = config["data"]
        required_any = {attrs_list_literal}
        for item in data.instances_by_klass("{element_class}"):
            if not any(item.get(a) for a in required_any):
                self._add_failure(
                    "No attributes specified; at least one required",
                    "{element_class}",
                    ", ".join(required_any),
                    data.path_by_id(item["id"]),
                )
        return self._result()
"""
    return TranslationResult(
        success=True,
        pattern="AT_LEAST_ONE_OF",
        python_body=body,
        notes=f"element={element_class!r} (from attr {nested_attr!r}), required_any={attrs}",
    )


TRANSLATORS = [
    try_cross_instance_unique,
    try_intra_attribute_unique,
    try_subset_check,
    try_incompat_codes,
    try_at_least_one,
]


def translate(
    jsonata: str, ddf_id: str, rule_text: str, attribute_hint: str = ""
) -> TranslationResult:
    for fn in TRANSLATORS:
        r = fn(jsonata, ddf_id, rule_text, attribute_hint)
        if r is not None:
            return r
    return TranslationResult(
        success=False,
        pattern="NO_MATCH",
        notes="No translator pattern matched this rule's JSONata.",
    )


# ──────────────────────────────────────────────────────────────────────────
# CLI (walking-skeleton debug)
# ──────────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--core-json", default="/sessions/lucid-eager-euler/mnt/core/rules/usdm/4-0.json")
    ap.add_argument("--only", default="", help="Comma-separated DDF ids to translate")
    ap.add_argument("--all-jsonata", action="store_true", help="Run on all 92 JSONata rules and report coverage")
    args = ap.parse_args()

    core_path = Path(args.core_json)
    if not core_path.exists():
        print(f"ERROR: CORE JSON not found at {core_path}", file=sys.stderr)
        return 1

    data = json.loads(core_path.read_text())
    jsonata_rules = []
    for r in data:
        cond = r.get("conditions")
        if isinstance(cond, str):
            ddf = r["reference"][0][0]["Rule_Identifier"]["Id"]
            desc = r.get("description", "")
            jsonata_rules.append((ddf, cond, desc))

    only = {s.strip().upper() for s in args.only.split(",") if s.strip()}
    if only:
        jsonata_rules = [t for t in jsonata_rules if t[0] in only]
    elif not args.all_jsonata:
        print("Specify --only <DDFxxxx> or --all-jsonata", file=sys.stderr)
        return 1

    from collections import Counter
    counter: Counter = Counter()
    for ddf, cond, desc in jsonata_rules:
        result = translate(cond, ddf, desc)
        counter[result.pattern] += 1
        if only or (not args.all_jsonata):
            # Detail mode: show each result
            print(f"\n=== {ddf}: {result.pattern} ===")
            print(f"  Text:  {desc[:110]}")
            print(f"  Notes: {result.notes}")
            if result.success:
                print("  Generated body:")
                for line in result.python_body.splitlines():
                    print(f"    {line}")

    print("\n=== Summary ===")
    for pat, n in counter.most_common():
        print(f"  {n:4d}  {pat}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
