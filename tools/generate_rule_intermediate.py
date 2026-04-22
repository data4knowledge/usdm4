"""
Stage 1 of the two-stage rule generator.

Reads:
  - DDF-RA/Deliverables/RULES/USDM_CORE_Rules.xlsx  (authoritative catalogue)
  - <core-cache>/rules/usdm/4-0.json                (CORE structured rules)

Writes:
  - usdm4/rules/intermediate/rule_ddf#####.yaml     (one per V4-applicable rule)

Each YAML captures what the generator can infer, leaving UNKNOWN markers where
it cannot. A human reviews/refines the YAML; stage 2 (generate_rule_python.py)
then consumes the reviewed YAML to emit rule_ddf#####.py + test_rule_ddf#####.py.

Classification per rule:
  HIGH_CT          — structured CORE conditions show a CT codelist check
  HIGH_REQUIRED    — structured CORE conditions show required-attribute
  HIGH_UNIQUE      — structured CORE conditions show is_not_unique_set
  HIGH_FORMAT      — structured CORE conditions show invalid_duration or regex
  HIGH_MUTEX       — structured CORE conditions show mutual exclusion
  MED_TEXT         — JSONata string, but rule text matches a known idiom
  LOW_CUSTOM       — JSONata string, rule text unclassifiable → hand-author
  STUB             — not in CORE (xlsx-only) → metadata-only YAML

Usage:
    python tools/generate_rule_intermediate.py                    # all rules
    python tools/generate_rule_intermediate.py --only DDF00104    # one rule
    python tools/generate_rule_intermediate.py --dry-run          # write to /tmp
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import openpyxl
import yaml

# ──────────────────────────────────────────────────────────────────────────
# Paths (resolved relative to this file when possible)
# ──────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]
XLSX_PATH = (
    REPO_ROOT.parent / "DDF-RA" / "Deliverables" / "RULES" / "USDM_CORE_Rules.xlsx"
)

# Default CORE cache location. Can be overridden via --core-json.
DEFAULT_CORE_JSON = (
    Path.home()
    / "Library"
    / "Caches"
    / "usdm4"
    / "core"
    / "rules"
    / "usdm"
    / "4-0.json"
)
# When running inside the Cowork sandbox, the Mac's Library cache is mounted at:
SANDBOX_CORE_JSON = Path("/sessions/lucid-eager-euler/mnt/core/rules/usdm/4-0.json")

OUTPUT_DIR = REPO_ROOT / "src" / "usdm4" / "rules" / "intermediate"
LIBRARY_DIR = REPO_ROOT / "src" / "usdm4" / "rules" / "library"

# ──────────────────────────────────────────────────────────────────────────
# xlsx reader
# ──────────────────────────────────────────────────────────────────────────


@dataclass
class XlsxRow:
    rule_id: str
    text: str
    severity: str  # "ERROR" | "WARNING"
    entity: str  # e.g. "Timing" or "Activity, Procedure"
    attrs: str  # e.g. "relativeToFrom"
    applies_v3: bool
    applies_v4: bool
    check_id: str


def read_xlsx(xlsx_path: Path) -> list[XlsxRow]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["Version 3.0 and 4.0 CORE rules"]
    rows: list[XlsxRow] = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0 or not row[6]:
            continue
        rows.append(
            XlsxRow(
                rule_id=str(row[6]).strip(),
                text=(row[0] or "").strip(),
                severity=(row[1] or "ERROR").strip(),
                entity=(row[2] or "").strip(),
                attrs=(row[3] or "").strip(),
                applies_v3=row[4] == "Y",
                applies_v4=row[5] == "Y",
                check_id=(row[7] or "").strip(),
            )
        )
    return rows


# ──────────────────────────────────────────────────────────────────────────
# CORE reader
# ──────────────────────────────────────────────────────────────────────────


def read_core(core_path: Path) -> dict[str, dict]:
    """Return CORE rules keyed by their primary DDF id."""
    raw = json.loads(core_path.read_text())
    by_ddf: dict[str, dict] = {}
    for r in raw:
        refs = r.get("reference") or []
        for sublist in refs:
            if not isinstance(sublist, list):
                continue
            for ref in sublist:
                rid = (ref.get("Rule_Identifier") or {}).get("Id")
                if rid and rid.startswith("DDF") and rid not in by_ddf:
                    by_ddf[rid] = r
                    break
    return by_ddf


def first_entity(entity_field: str) -> str:
    """Pick the first class when multiple are listed (e.g. 'Activity, Procedure')."""
    return re.split(r"[,;/]", entity_field)[0].strip()


def first_attr(attrs_field: str) -> str:
    return re.split(r"[,;/]", attrs_field)[0].strip()


# ──────────────────────────────────────────────────────────────────────────
# CORE condition walker
# ──────────────────────────────────────────────────────────────────────────


@dataclass
class WalkedConditions:
    """What we extract from a CORE conditions tree."""

    instance_type: Optional[str] = None  # e.g. "Timing"
    rel_type: Optional[str] = None  # e.g. "definition"
    # List of (operator, target, comparator) tuples for non-filter checks
    checks: list[tuple[str, str, Any]] = field(default_factory=list)
    # Structural flags
    has_not: bool = False
    has_any: bool = False
    is_jsonata_string: bool = False
    raw: Any = None


def walk_core_conditions(cond: Any) -> WalkedConditions:
    w = WalkedConditions(raw=cond)
    if isinstance(cond, str):
        w.is_jsonata_string = True
        return w
    if not isinstance(cond, dict):
        return w

    def visit(node: Any):
        if isinstance(node, dict):
            if "any" in node:
                w.has_any = True
                visit(node["any"])
                return
            if "not" in node:
                w.has_not = True
                visit(node["not"])
                return
            if "all" in node:
                visit(node["all"])
                return
            if "operator" in node:
                op = node["operator"]
                val = node.get("value", {}) or {}
                target = val.get("target")
                comparator = val.get("comparator")
                # Filter conditions that set context
                if (
                    op == "equal_to"
                    and target == "instanceType"
                    and isinstance(comparator, str)
                ):
                    w.instance_type = comparator
                    return
                if (
                    op == "equal_to"
                    and target == "rel_type"
                    and isinstance(comparator, str)
                ):
                    w.rel_type = comparator
                    return
                # Everything else is a real check
                w.checks.append((op, target, comparator))
        elif isinstance(node, list):
            for x in node:
                visit(x)

    visit(cond)
    return w


# ──────────────────────────────────────────────────────────────────────────
# Existing-implementation introspection
# ──────────────────────────────────────────────────────────────────────────
#
# When usdm4/rules/library/rule_ddf#####.py already has a working validate()
# body (e.g. one of the 25 v3 implementations we just inlined), that code is
# the authoritative source of truth — stage 1 should:
#   1. Mark the rule HAS_IMPLEMENTATION so stage 2 doesn't overwrite it.
#   2. Populate YAML fields by introspecting the working code, not by
#      guessing from CORE or rule text. If CORE would have inferred a
#      different predicate, surface that as a cross-check signal.


def is_stub_body(validate_body: str) -> bool:
    """Detect a NotImplementedError-only stub body."""
    if "raise NotImplementedError" not in validate_body:
        return False
    # Allow a one-or-two-line body that raises NotImplementedError.
    non_blank = [line for line in validate_body.splitlines() if line.strip()]
    # Stubs are ~3 lines: signature, optional comment, raise
    return len(non_blank) <= 4


def extract_validate_body(source: str) -> Optional[str]:
    """Return the validate() method's body, or None if the file has no validate."""
    m = re.search(r"def validate\(self.*?(?=\n    def |\nclass |\Z)", source, re.S)
    return m.group(0) if m else None


def introspect_implementation(path: Path) -> Optional[dict]:
    """
    If the file at path has a real validate() body (not a stub), return a dict
    describing what the code actually does. Return None for stubs or missing
    files — those rules need regular classification.

    Introspection looks at the whole file (not just the validate body) because
    many rules delegate to a _validate() helper where instances_by_klass and
    parent_by_klass are actually called.
    """
    if not path.exists():
        return None
    text = path.read_text()
    validate_body = extract_validate_body(text)
    if validate_body is None or is_stub_body(validate_body):
        return None

    extracted: dict[str, Any] = {}

    # Shortcut: _ct_check(config, "Class", "attr") → CT-member, one-liner form
    ct = re.search(r'_ct_check\(\s*config,\s*"(\w+)",\s*"(\w+)"\s*\)', text)
    if ct:
        extracted["class"] = ct.group(1)
        extracted["attribute"] = ct.group(2)
        extracted["predicate"] = "ct-member"
        return extracted

    # Primary iteration class via instances_by_klass("X") — anywhere in file
    klass_calls = re.findall(r'instances_by_klass\(\s*"(\w+)"\s*\)', text)
    if klass_calls:
        distinct = list(dict.fromkeys(klass_calls))  # preserve order, dedupe
        extracted["class"] = distinct[0]
        if len(distinct) > 1:
            extracted["also_iterates"] = distinct[1:]

    # Scope: parent_by_klass(id, ["X", "Y", ...]) — the scope-list form
    parent_list = re.search(r"parent_by_klass\([^,]+,\s*\[([^\]]+)\]", text)
    if parent_list:
        scope_klasses = re.findall(r'"(\w+)"', parent_list.group(1))
        if scope_klasses:
            extracted["scope"] = {"type": "parent-of-class", "klasses": scope_klasses}
    else:
        # Bare form: parent_by_klass(id, klass_list) where klass_list is a parameter
        if "parent_by_klass" in text:
            # Pull the default scope from validate() -> self._validate(..., [...])
            default_scope = re.search(
                r"return self\._validate\(\s*config,\s*\[([^\]]+)\]", text
            )
            if default_scope:
                scope_klasses = re.findall(r'"(\w+)"', default_scope.group(1))
                if scope_klasses:
                    extracted["scope"] = {
                        "type": "parent-of-class",
                        "klasses": scope_klasses,
                    }

    # Failure messages (useful preview for the reviewer)
    msgs = re.findall(r'_add_failure\(\s*f?"([^"]+)"', text)
    if msgs:
        extracted["failure_messages"] = msgs[:4]  # cap the preview

    # Predicate inference from code shape (ordered, first-match wins).
    # Use the whole file text so helpers in _validate() are considered.
    if "SchemaValidation" in text or "schema_path" in text:
        extracted["predicate"] = "schema-conformance"
    elif "parent_by_klass" in text and (
        "item_parent" in text or 'parent["id"]' in text or "parent['id']" in text
    ):
        extracted["predicate"] = "cross-reference-same-scope"
    elif re.search(r'if\s+"\w+"\s+not\s+in\s+item', text) and re.search(
        r'item\["type"\]|item\[.type.\]', text
    ):
        extracted["predicate"] = "conditional-required-attribute"
    elif re.search(r'if\s+"\w+"\s+not\s+in\s+item', text):
        extracted["predicate"] = "required-attribute"
    elif "both" in text.lower() and re.search(
        r"instance_by_id\([^)]+\).*instance_by_id\(", text, re.S
    ):
        extracted["predicate"] = "mutual-exclusion"
    elif "_validate_version" in text:
        extracted["predicate"] = "version-check"
    elif "address_valid" in text or re.search(
        r'attribute\s+in\s+\[.*"text".*"line"', text, re.S
    ):
        extracted["predicate"] = "at-least-one-of"
    else:
        extracted["predicate"] = "custom"

    # Attribute hint: pull the first `attribute not in item` reference if we
    # haven't already set one.
    if "attribute" not in extracted:
        attr_hit = re.search(r'"(\w+[Ii]d|\w+)"\s+not\s+in\s+item', text)
        if attr_hit:
            extracted["attribute"] = attr_hit.group(1)

    return extracted


# ──────────────────────────────────────────────────────────────────────────
# Predicate inference
# ──────────────────────────────────────────────────────────────────────────


# Rule-text idioms (used when CORE conditions are a JSONata string).
RE_CT = re.compile(
    r"must be specified (using|according to).*codelist|must conform (to|with) the .*codelist",
    re.I,
)
RE_UNIQUE = re.compile(
    r"must be unique|must not (have|contain) duplicate|must not be referenced more than once|expected to be unique",
    re.I,
)
RE_REQUIRED = re.compile(
    r"must be (defined|specified|given|provided|included)|at least one|must have (at least|exactly)",
    re.I,
)
RE_MUTEX = re.compile(r"but not both|must not be defined|mutually exclusive", re.I)
RE_BICONDITIONAL = re.compile(r"\bvice versa\b|\bwhile if\b", re.I)
RE_IMPLICATION = re.compile(r"\bif\b[^.]*\bthen\b", re.I)  # checked after biconditional
RE_CONDITIONAL = re.compile(r"\bif\b.*\bthen\b|when .*must|and vice versa", re.I)
RE_IDREF = re.compile(r"must reference|must refer to|must only reference", re.I)
RE_FORMAT = re.compile(
    r"iso 8601|must be formatted|non-negative|duration|must match the pattern", re.I
)


def infer_from_core(walked: WalkedConditions) -> Optional[dict]:
    """
    Return a predicate dict inferred from structured CORE conditions, or None
    if the conditions don't fit a known pattern.

    Condition semantics in CORE: conditions describe when the rule FAILS.
    """
    if walked.is_jsonata_string or not walked.checks:
        return None

    ops = [c[0] for c in walked.checks]
    unique_ops = set(ops)

    # CT-codelist: has is_contained_by or is_not_contained_by
    if {"is_contained_by", "is_not_contained_by"} & unique_ops:
        # Target usually looks like "attr.code" or "attr.decode" — strip suffix for the attribute
        targets = [
            c[1]
            for c in walked.checks
            if c[0] in ("is_contained_by", "is_not_contained_by")
        ]
        tgt = targets[0] if targets else None
        attr = tgt.split(".")[0] if tgt else None
        # comparator in CORE is often a JSONata variable ($valid_versions etc.),
        # not the actual codelist id. The C##### id is reliably in the rule text.
        # Leave codelist_ref population to the caller (who has the rule text).
        return {
            "predicate": "ct-member",
            "attribute": attr,
        }

    # Uniqueness: is_not_unique_set
    if "is_not_unique_set" in unique_ops:
        tgt = next((c[1] for c in walked.checks if c[0] == "is_not_unique_set"), None)
        return {"predicate": "unique-within-scope", "attribute": tgt}

    # Format: invalid_duration or not_matches_regex
    if "invalid_duration" in unique_ops:
        tgt = next((c[1] for c in walked.checks if c[0] == "invalid_duration"), None)
        return {"predicate": "format", "attribute": tgt, "format": "iso8601-duration"}
    if "not_matches_regex" in unique_ops:
        tgt = next((c[1] for c in walked.checks if c[0] == "not_matches_regex"), None)
        return {"predicate": "format", "attribute": tgt, "format": "regex"}

    # Required-attribute: single empty check (without other shape markers)
    # When the condition says "attr is empty" that's the failure → rule requires attr to be non-empty.
    if ops.count("empty") == 1 and unique_ops <= {"empty", "exists", "non_empty"}:
        tgt = next((c[1] for c in walked.checks if c[0] == "empty"), None)
        return {"predicate": "required-attribute", "attribute": tgt}

    # Mutual exclusion: multiple non_empty/exists on different attrs (all conjunction)
    if not walked.has_any and not walked.has_not:
        nonempty_targets = [
            c[1] for c in walked.checks if c[0] in ("non_empty", "exists")
        ]
        if len(set(nonempty_targets)) >= 2:
            return {
                "predicate": "mutual-exclusion",
                "attributes": sorted(set(nonempty_targets)),
            }

    return None


def infer_from_text(text: str) -> Optional[str]:
    """Fallback classifier when CORE is a JSONata string. Returns predicate or None."""
    if RE_CT.search(text):
        return "ct-member"
    if RE_UNIQUE.search(text):
        return "unique-within-scope"
    if RE_MUTEX.search(text):
        return "mutual-exclusion"
    if RE_IDREF.search(text):
        return "id-reference-resolves"
    # Biconditional is a more specific case of conditional — check it first.
    if RE_BICONDITIONAL.search(text):
        return "biconditional"
    # Plain "if X then Y" (one-way) — the template fills in when side specs
    # are provided in the YAML, otherwise falls through to a stub.
    if RE_IMPLICATION.search(text):
        return "implication"
    if RE_CONDITIONAL.search(text):
        return "conditional"
    if RE_FORMAT.search(text):
        return "format"
    if RE_REQUIRED.search(text):
        return "required-attribute"
    return None


# ──────────────────────────────────────────────────────────────────────────
# Scope inference (mostly rule-text based)
# ──────────────────────────────────────────────────────────────────────────

# Common phrases that imply a parent-of-class scope.
SCOPE_PATTERNS = [
    (
        re.compile(r"within (?:a|each|the same) study design", re.I),
        ("parent-of-class", ["InterventionalStudyDesign", "ObservationalStudyDesign"]),
    ),
    (
        re.compile(r"within (?:a|each|the) study version", re.I),
        ("parent-of-class", ["StudyVersion"]),
    ),
    (
        re.compile(r"within (?:a|each|the same) activity", re.I),
        ("parent-of-class", ["Activity"]),
    ),
    (
        re.compile(r"within (?:a|each|the same) encounter", re.I),
        ("parent-of-class", ["Encounter"]),
    ),
    (
        re.compile(r"within (?:a|each|the same) timeline", re.I),
        ("parent-of-class", ["ScheduleTimeline"]),
    ),
    (
        re.compile(r"for (?:a|each|the) study version", re.I),
        ("parent-of-class", ["StudyVersion"]),
    ),
]


def infer_scope(text: str) -> Optional[dict]:
    for pat, (scope_type, klasses) in SCOPE_PATTERNS:
        if pat.search(text):
            return {"type": scope_type, "klasses": klasses}
    return None


# ──────────────────────────────────────────────────────────────────────────
# Build intermediate
# ──────────────────────────────────────────────────────────────────────────


def extract_action_message(core_rule: dict) -> Optional[str]:
    for a in core_rule.get("actions") or []:
        msg = (a.get("params") or {}).get("message")
        if msg:
            return msg
    return None


def extract_entity_from_core(walked: WalkedConditions, xlsx: XlsxRow) -> str:
    """Prefer CORE's detected instanceType; fall back to xlsx 'Applies to'."""
    if walked.instance_type:
        return walked.instance_type
    e = xlsx.entity.strip()
    if e.lower() == "all":
        return "All"
    return first_entity(e)


def build_intermediate(xlsx: XlsxRow, core_rule: Optional[dict]) -> dict:
    """Produce the intermediate YAML dict for one rule."""
    data: dict[str, Any] = {
        "id": xlsx.rule_id,
        "check_id": xlsx.check_id or None,
        "severity": xlsx.severity,
        "text": xlsx.text,
    }

    xlsx_entity = xlsx.entity.strip()
    xlsx_attr = xlsx.attrs.strip()
    data["entity"] = xlsx_entity or "UNKNOWN"
    data["attributes"] = xlsx_attr or "UNKNOWN"

    # ── HIGHEST PRIORITY: existing implementation ─────────────────────────
    # If rule_ddf#####.py already has a real validate() body, that code is
    # authoritative. Build the YAML from the code, and only use CORE as a
    # cross-check signal.
    impl_path = LIBRARY_DIR / f"rule_{xlsx.rule_id.lower()}.py"
    impl_info = introspect_implementation(impl_path)
    if impl_info is not None:
        data["classification"] = "HAS_IMPLEMENTATION"
        data["source"] = "existing-code"
        data["confidence"] = "high"
        data["review_required"] = False
        data["implementation_file"] = str(impl_path.relative_to(REPO_ROOT))
        # Overlay the extracted fields
        for k, v in impl_info.items():
            data[k] = v
        # Attach CORE's inference as a cross-check if we have one and it differs
        if core_rule is not None:
            walked = walk_core_conditions(core_rule.get("conditions"))
            core_pred = infer_from_core(walked)
            action_msg = extract_action_message(core_rule)
            if action_msg:
                data["core_message"] = action_msg
            if core_pred is not None and core_pred.get("predicate") != impl_info.get(
                "predicate"
            ):
                data["core_inference_mismatch"] = {
                    "core_says": core_pred.get("predicate"),
                    "code_says": impl_info.get("predicate"),
                }
        return data

    # ── No existing implementation — classify from CORE + text ────────────
    if core_rule is None:
        data["source"] = "xlsx-only"
        data["predicate"] = "custom"
        data["classification"] = "STUB"
        data["confidence"] = "low"
        data["review_required"] = True
        return data

    walked = walk_core_conditions(core_rule.get("conditions"))
    message = extract_action_message(core_rule)
    if message:
        data["message"] = message

    # Use CORE's instanceType if present
    data["class"] = extract_entity_from_core(walked, xlsx)

    # Infer predicate from structured CORE first, then text fallback
    predicate_info = infer_from_core(walked)
    if predicate_info is not None:
        data["source"] = "core-structured"
        data["predicate"] = predicate_info["predicate"]
        # Overlay attribute/extra keys onto data
        for k, v in predicate_info.items():
            if k == "predicate":
                continue
            data[k] = v
        data["classification"] = (
            f"HIGH_{predicate_info['predicate'].replace('-', '_').upper()}"
        )
        data["confidence"] = "high"
        data["review_required"] = False
        # For CT-member, extract the C##### codelist id from the rule text
        if predicate_info["predicate"] == "ct-member":
            m = re.search(r"\((C\d{5,6})\)", xlsx.text)
            if m:
                data["codelist_ref"] = m.group(1)
    else:
        # JSONata string or unrecognised structured pattern — fall back to text
        text_pred = infer_from_text(xlsx.text)
        if text_pred:
            data["source"] = "rule-text"
            data["predicate"] = text_pred
            data["classification"] = "MED_TEXT"
            data["confidence"] = "medium"
            data["review_required"] = True
        else:
            data["source"] = "rule-text"
            data["predicate"] = "custom"
            data["classification"] = "LOW_CUSTOM"
            data["confidence"] = "low"
            data["review_required"] = True

    # Scope inference from text (regardless of predicate source)
    scope = infer_scope(xlsx.text)
    if scope is not None:
        data["scope"] = scope

    # Preserve the JSONata string as a reference comment for human review
    if walked.is_jsonata_string:
        data["_core_jsonata_reference"] = walked.raw
    elif walked.has_not or walked.has_any:
        # Complex structured conditions — include raw for reviewer
        data["_core_conditions_reference"] = core_rule.get("conditions")

    return data


# ──────────────────────────────────────────────────────────────────────────
# Writer
# ──────────────────────────────────────────────────────────────────────────


def render_yaml(data: dict) -> str:
    """Emit YAML with a stable, review-friendly key order and a header comment."""
    # Preferred key order
    order = [
        "id",
        "check_id",
        "severity",
        "classification",
        "confidence",
        "source",
        "review_required",
        "implementation_file",
        "predicate",
        "class",
        "entity",
        "attribute",
        "attributes",
        "also_iterates",
        "codelist_ref",
        "format",
        "scope",
        "text",
        "message",
        "core_message",
        "failure_messages",
        "core_inference_mismatch",
        "_core_jsonata_reference",
        "_core_conditions_reference",
    ]
    ordered = {}
    for k in order:
        if k in data:
            ordered[k] = data[k]
    # Append anything else
    for k, v in data.items():
        if k not in ordered:
            ordered[k] = v

    header = (
        f"# {data['id']} — {data.get('classification', '?')} — auto-generated by tools/generate_rule_intermediate.py\n"
        f"# Source: {data.get('source', '?')}\n"
    )
    body = yaml.safe_dump(
        ordered,
        sort_keys=False,
        default_flow_style=False,
        width=200,
        allow_unicode=True,
    )
    return header + body


# ──────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--core-json",
        default=None,
        help=f"Path to CORE rules JSON (default: tries {SANDBOX_CORE_JSON} then {DEFAULT_CORE_JSON})",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Write to /tmp/usdm4_intermediate instead of the real output dir",
    )
    ap.add_argument(
        "--only", default="", help="Only process the listed DDF ids (comma-separated)"
    )
    ap.add_argument(
        "--xlsx", default=str(XLSX_PATH), help=f"Path to xlsx (default: {XLSX_PATH})"
    )
    args = ap.parse_args()

    # Resolve CORE JSON path
    if args.core_json:
        core_path = Path(args.core_json)
    elif SANDBOX_CORE_JSON.exists():
        core_path = SANDBOX_CORE_JSON
    elif DEFAULT_CORE_JSON.exists():
        core_path = DEFAULT_CORE_JSON
    else:
        print(
            f"ERROR: no CORE rules JSON found. Tried {SANDBOX_CORE_JSON} and {DEFAULT_CORE_JSON}.",
            file=sys.stderr,
        )
        print(
            "Pass --core-json <path> or run tools/prepare_core_cache.py first.",
            file=sys.stderr,
        )
        return 1

    xlsx_path = Path(args.xlsx)
    if not xlsx_path.exists():
        print(f"ERROR: xlsx not found at {xlsx_path}", file=sys.stderr)
        return 1

    print(f"xlsx:       {xlsx_path}", file=sys.stderr)
    print(f"CORE JSON:  {core_path}", file=sys.stderr)

    rows = read_xlsx(xlsx_path)
    core_by_ddf = read_core(core_path)
    v4_rows = [r for r in rows if r.applies_v4]

    only = {s.strip().upper() for s in args.only.split(",") if s.strip()}

    out_dir = Path("/tmp/usdm4_intermediate") if args.dry_run else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    from collections import Counter

    cls_counter: Counter = Counter()
    written = 0
    preserved = 0
    for row in v4_rows:
        if only and row.rule_id.upper() not in only:
            continue
        core_rule = core_by_ddf.get(row.rule_id)
        data = build_intermediate(row, core_rule)
        cls_counter[data["classification"]] += 1
        out_path = out_dir / f"rule_{row.rule_id.lower()}.yaml"
        # Preserve hand-edited YAMLs that carry the MANUAL sentinel. Stage-2
        # reads these as-is and the human's field completions survive.
        if out_path.exists() and "# MANUAL: do not regenerate" in out_path.read_text():
            preserved += 1
            continue
        out_path.write_text(render_yaml(data))
        written += 1

    print(f"\nWrote {written} intermediate YAML(s) to {out_dir}", file=sys.stderr)
    if preserved:
        print(
            f"Preserved {preserved} YAML(s) with MANUAL sentinel (hand-edited, not regenerated)",
            file=sys.stderr,
        )
    print("By classification:", file=sys.stderr)
    for cls, n in sorted(cls_counter.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {n:4d}  {cls}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
