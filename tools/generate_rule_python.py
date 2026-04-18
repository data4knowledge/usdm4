"""
Stage 2 of the two-stage rule generator.

Reads:
  src/usdm4/rules/intermediate/rule_ddf#####.yaml    (produced by stage 1)

Writes (or skips, based on YAML classification):
  src/usdm4/rules/library/rule_ddf#####.py           — rule class + validate()
  tests/usdm4/rules/test_rule_ddf#####.py            — metadata + test scaffold

Dispatch on YAML `classification`:

  HAS_IMPLEMENTATION         — rule file untouched (working code already there),
                               test file emitted with metadata assertions only.
  HIGH_CT_MEMBER             — one-liner self._ct_check(config, klass, attr).
  HIGH_UNIQUE_WITHIN_SCOPE   — DataStore-based uniqueness loop, parent_by_klass scope.
  HIGH_FORMAT                — ISO 8601 duration / regex format helper.
  HIGH_REQUIRED_ATTRIBUTE    — attribute-presence check.
  MED_TEXT / LOW_CUSTOM      — try the JSONata translator; fall back to a stub
                               with TODO + the CORE JSONata preserved as reference.
  STUB                       — metadata-only stub with TODO.

The stub bodies raise NotImplementedError so the lock-in tests fail loudly
once someone implements a rule without adding a real test.

Usage:
    python tools/generate_rule_python.py                      # write to real paths
    python tools/generate_rule_python.py --dry-run            # write to /tmp
    python tools/generate_rule_python.py --only DDF00104      # one rule
    python tools/generate_rule_python.py --no-tests           # skip test files
    python tools/generate_rule_python.py --no-rules           # skip rule files
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

import yaml

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from translate_jsonata import translate  # noqa: E402

# ──────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]
INTERMEDIATE_DIR = REPO_ROOT / "src" / "usdm4" / "rules" / "intermediate"
LIBRARY_DIR = REPO_ROOT / "src" / "usdm4" / "rules" / "library"
TESTS_DIR = REPO_ROOT / "tests" / "usdm4" / "rules"


# ──────────────────────────────────────────────────────────────────────────
# Python literal helpers
# ──────────────────────────────────────────────────────────────────────────


def py_str(s: str) -> str:
    """Python string literal. Prefer single quotes when string contains double quotes."""
    if '"' in s and "'" not in s:
        return "'" + s + "'"
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def class_name(rule_id: str) -> str:
    return f"Rule{rule_id}"


# ──────────────────────────────────────────────────────────────────────────
# Rule file header (common across every classification)
# ──────────────────────────────────────────────────────────────────────────

RULE_HEADER_TMPL = '''\
from usdm4.rules.rule_template import RuleTemplate


class {cls}(RuleTemplate):
    """
    {rid}: {text_docstring}

    Applies to: {entity}
    Attributes: {attrs}
    """

    def __init__(self):
        super().__init__(
            {rid_str},
            RuleTemplate.{severity},
            {text_str},
        )
'''


def render_header(data: dict) -> str:
    rid = data["id"]
    severity = data.get("severity", "ERROR").upper()
    if severity not in ("ERROR", "WARNING"):
        severity = "ERROR"
    text = (data.get("text") or "").replace("\n", " ")
    entity = data.get("entity") or data.get("class") or "(see text)"
    attrs = data.get("attributes") or data.get("attribute") or "(see text)"
    return RULE_HEADER_TMPL.format(
        cls=class_name(rid),
        rid=rid,
        text_docstring=text,
        entity=entity,
        attrs=attrs,
        rid_str=py_str(rid),
        severity=severity,
        text_str=py_str(text),
    )


# ──────────────────────────────────────────────────────────────────────────
# Body renderers — one per classification
# ──────────────────────────────────────────────────────────────────────────


_CT_LIBRARY = None  # lazy singleton


def _ct_library():
    """Load the CT library once for codelist existence checks at generation time."""
    global _CT_LIBRARY
    if _CT_LIBRARY is not None:
        return _CT_LIBRARY
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from usdm4.ct.cdisc.library import Library as CTLibrary  # noqa: E402
    lib = CTLibrary(str(REPO_ROOT / "src" / "usdm4"))
    lib.load()
    _CT_LIBRARY = lib
    return lib


def _ct_codelist_exists(klass: str, attr: str) -> bool:
    """Return True if CT has a codelist registered for (klass, attr)."""
    try:
        lib = _ct_library()
        return lib.klass_and_attribute(klass, attr) is not None
    except Exception:
        return False


def render_body_ct(data: dict) -> tuple[str, bool]:
    """
    CT-codelist membership check. Returns (body, is_implemented).

    Guards:
    - "All" / "validator" / empty class/attribute → schema-conformance rule,
      not a real CT lookup. Stub it.
    - (klass, attr) pair not registered in the CT library → the generated
      _ct_check would raise CTException at runtime. Stub it with a note.
    """
    cls = data.get("class") or data.get("entity", "").split(",")[0].strip()
    attr = data.get("attribute") or data.get("attributes", "").split(",")[0].strip()
    if cls in ("All", "", None) or attr in ("All", "", None, "validator"):
        return _stub_body(
            data,
            reason=f"HIGH_CT_MEMBER with class={cls!r} attr={attr!r} — likely a "
                   "schema-conformance rule, not CT lookup. Needs hand-authoring.",
        ), False
    if not _ct_codelist_exists(cls, attr):
        return _stub_body(
            data,
            reason=f"HIGH_CT_MEMBER with no CT codelist registered for "
                   f"({cls!r}, {attr!r}). Update ct_config.yaml or revise the "
                   "rule's class/attribute before implementing.",
        ), False
    return f'''
    def validate(self, config: dict) -> bool:
        return self._ct_check(config, "{cls}", "{attr}")
''', True


def render_body_required_attribute(data: dict) -> str:
    cls = data.get("class") or data.get("entity", "").split(",")[0].strip()
    attr = data.get("attribute") or data.get("attributes", "").split(",")[0].strip()
    return f'''
    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("{cls}"):
            if not item.get("{attr}"):
                self._add_failure(
                    "Required attribute '{attr}' is missing or empty",
                    "{cls}",
                    "{attr}",
                    data.path_by_id(item["id"]),
                )
        return self._result()
'''


def render_body_unique(data: dict) -> tuple[str, bool]:
    """
    Cross-instance uniqueness within a parent-class scope.

    Returns (body, is_implemented). Without explicit scope information,
    uniqueness is ambiguous (global vs per-parent vs intra-list-attribute),
    so we emit a stub rather than guess — guessing produces false positives
    that swamp the finding list.

    Disambiguation: when the CORE-inferred class (data['class']) disagrees
    with the xlsx entity (data['entity']) AND the xlsx attribute looks like
    a list (plural / ends with Ids), interpret the rule as intra-attribute
    uniqueness on the xlsx entity's list — not cross-instance on the CORE
    class. CORE's conditions often walk into list-element classes (e.g.
    Code) even when the semantic rule is about the parent's list.
    """
    cls = data.get("class") or data.get("entity", "").split(",")[0].strip()
    attr = data.get("attribute") or data.get("attributes", "").split(",")[0].strip()
    entity = (data.get("entity") or "").split(",")[0].strip()
    xlsx_attr = (data.get("attributes") or "").split(",")[0].strip()

    # Intra-attribute uniqueness: when CORE walked into a child class but the
    # rule is really about uniqueness within the parent's list attribute.
    looks_plural = (
        xlsx_attr
        and (xlsx_attr.endswith("s") or xlsx_attr.endswith("Ids"))
        and not xlsx_attr.endswith("ss")
    )
    if entity and entity != cls and looks_plural and entity != "All":
        key_attr = attr if attr != xlsx_attr else "code"  # CORE's attribute is the sub-field
        body = f'''
    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("{entity}"):
            values = []
            for sub in item.get("{xlsx_attr}") or []:
                v = sub.get("{key_attr}") if isinstance(sub, dict) else sub
                if v not in (None, ""):
                    values.append(v)
            if len(values) != len(set(values)):
                dupes = sorted(set(v for v in values if values.count(v) > 1))
                self._add_failure(
                    f"Duplicate {xlsx_attr} entries: {{dupes!r}}",
                    "{entity}",
                    "{xlsx_attr}",
                    data.path_by_id(item["id"]),
                )
        return self._result()
'''
        return body, True

    scope = data.get("scope")
    if isinstance(scope, dict) and scope.get("type") == "parent-of-class":
        scope_classes = scope.get("klasses") or []
        scope_literal = repr(scope_classes)
        body = f'''
    def validate(self, config: dict) -> bool:
        data = config["data"]
        seen: dict = {{}}
        for item in data.instances_by_klass("{cls}"):
            scope = data.parent_by_klass(item["id"], {scope_literal})
            if scope is None:
                continue
            value = item.get("{attr}")
            if value in (None, "", [], {{}}):
                continue
            key = (scope["id"], value)
            if key in seen:
                self._add_failure(
                    f"Duplicate {attr} {{value!r}} within scope",
                    "{cls}",
                    "{attr}",
                    data.path_by_id(item["id"]),
                )
            else:
                seen[key] = item["id"]
        return self._result()
'''
        return body, True

    # No scope info — stub, flagged as needing review. Uniqueness without
    # scope is ambiguous: could be global, per-parent, or intra-attribute.
    return _stub_body(
        data,
        reason="HIGH_UNIQUE_WITHIN_SCOPE without scope info — ambiguous "
               "(global vs per-parent vs intra-attribute). Review rule text.",
    ), False


def render_body_format(data: dict) -> str:
    cls = data.get("class") or data.get("entity", "").split(",")[0].strip()
    attr = data.get("attribute") or data.get("attributes", "").split(",")[0].strip()
    fmt = data.get("format") or "regex"
    if fmt == "iso8601-duration":
        return f'''
    def validate(self, config: dict) -> bool:
        import re
        # ISO 8601 duration — optional leading "-" (negative), but CORE convention
        # requires non-negative here. Anchors at start/end.
        pat = re.compile(
            r"^P(?!$)(\\d+(?:\\.\\d+)?Y)?(\\d+(?:\\.\\d+)?M)?(\\d+(?:\\.\\d+)?W)?(\\d+(?:\\.\\d+)?D)?"
            r"(T(\\d+(?:\\.\\d+)?H)?(\\d+(?:\\.\\d+)?M)?(\\d+(?:\\.\\d+)?S)?)?$"
        )
        data = config["data"]
        for item in data.instances_by_klass("{cls}"):
            v = item.get("{attr}")
            if not v:
                continue
            if not pat.match(str(v)):
                self._add_failure(
                    f"'{{v}}' is not a non-negative ISO 8601 duration",
                    "{cls}",
                    "{attr}",
                    data.path_by_id(item["id"]),
                )
        return self._result()
'''
    # Generic regex — without a pattern, we can only stub.
    return _stub_body(data, reason=f"HIGH_FORMAT with format={fmt!r} but no pattern available")


def render_body_from_jsonata(data: dict) -> Optional[str]:
    """Try the translator against CORE JSONata captured in the YAML."""
    jsonata = data.get("_core_jsonata_reference")
    if not isinstance(jsonata, str):
        return None
    result = translate(jsonata, data["id"], data.get("text", ""))
    if not result.success:
        return None
    return "\n" + result.python_body


def _stub_body(data: dict, reason: str) -> str:
    jsonata = data.get("_core_jsonata_reference")
    reference_block = ""
    if isinstance(jsonata, str) and jsonata.strip():
        indented = "\n".join("    #     " + line for line in jsonata.splitlines())
        reference_block = f"""
    # Reference — CORE JSONata condition (semantics, not executed):
{indented}
"""
    return f'''
    # TODO: implement. {reason}{reference_block}
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("{data['id']}: not yet implemented")
'''


def render_rule_body(data: dict) -> tuple[str, bool]:
    """
    Dispatch on classification. Returns (body, is_implemented) where
    is_implemented=True means the body has a real validate() and the test
    renderer should NOT emit a NotImplementedError lock-in test.
    """
    cls = data.get("classification", "STUB")

    if cls == "HIGH_CT_MEMBER":
        return render_body_ct(data)  # returns (body, bool)
    if cls == "HIGH_REQUIRED_ATTRIBUTE":
        return render_body_required_attribute(data), True
    if cls == "HIGH_UNIQUE_WITHIN_SCOPE":
        return render_body_unique(data)  # already returns (body, bool)
    if cls == "HIGH_FORMAT":
        fmt = data.get("format")
        if fmt == "iso8601-duration":
            return render_body_format(data), True
        # Generic regex with no pattern → stub
        return render_body_format(data), False

    # MED_TEXT / LOW_CUSTOM — try the JSONata translator, else stub.
    if cls in ("MED_TEXT", "LOW_CUSTOM"):
        translated = render_body_from_jsonata(data)
        if translated is not None:
            return translated, True
        return _stub_body(data, reason=f"{cls}: JSONata translator did not match a known pattern"), False

    # STUB: xlsx-only, no CORE entry
    return _stub_body(data, reason="STUB: rule not present in CORE catalogue"), False


# ──────────────────────────────────────────────────────────────────────────
# Test file renderer
# ──────────────────────────────────────────────────────────────────────────


def render_test_file(data: dict, is_implemented: bool) -> str:
    """
    Emit a pytest module for one rule.

    `is_implemented` reflects the actual state of the rule body produced by
    render_rule_body — HAS_IMPLEMENTATION rules and any rule where the
    generator emitted a real validate() (HIGH_* or translated JSONata) get
    pass/fail skeleton tests. Only genuine NotImplementedError stubs get the
    lock-in test.
    """
    rid = data["id"]
    cls = class_name(rid)
    severity = data.get("severity", "ERROR").upper()
    if severity not in ("ERROR", "WARNING"):
        severity = "ERROR"
    text = (data.get("text") or "").replace("\n", " ")
    classification = data.get("classification", "STUB")

    header = f'''"""Generated by tools/generate_rule_python.py — classification: {classification}"""

import pytest
from usdm4.rules.library.rule_{rid.lower()} import {cls}
from usdm4.rules.rule_template import RuleTemplate


class Test{cls}:
    def test_metadata(self):
        rule = {cls}()
        assert rule._rule == {py_str(rid)}
        assert rule._level == RuleTemplate.{severity}
        assert rule._rule_text == {py_str(text)}
'''

    if is_implemented:
        # Rule has a real validate() — either HAS_IMPLEMENTATION, a HIGH_*
        # generator template, or a translated JSONata body. Fixtures are a
        # human-authored job; mark the scenario tests skipped with TODOs.
        body = '''
    @pytest.mark.skip(reason="TODO: craft positive fixture (valid USDM, rule accepts)")
    def test_valid_data_passes(self):
        pass

    @pytest.mark.skip(reason="TODO: craft negative fixture (invalid USDM, rule flags)")
    def test_invalid_data_fails(self):
        pass
'''
    else:
        # NotImplementedError stub — lock the behaviour in so the test fails
        # the moment someone implements the rule without writing real tests.
        body = f'''
    def test_not_implemented(self):
        """Lock-in: fails the moment the rule gains a real validate() body."""
        rule = {cls}()
        with pytest.raises(NotImplementedError):
            rule.validate({{"data": None, "ct": None}})
'''

    return header + body


# ──────────────────────────────────────────────────────────────────────────
# Emission
# ──────────────────────────────────────────────────────────────────────────


def emit_rule_and_test(
    data: dict,
    rule_dir: Path,
    test_dir: Path,
    *,
    write_rule: bool,
    write_test: bool,
    overwrite_tests: bool,
) -> dict:
    """Return a dict of what was written / skipped for this rule."""
    rid = data["id"].lower()
    cls = data.get("classification", "STUB")
    rule_path = rule_dir / f"rule_{rid}.py"
    test_path = test_dir / f"test_rule_{rid}.py"
    report: dict[str, Any] = {"rid": data["id"], "classification": cls, "rule_written": False, "test_written": False, "test_skipped": None}

    # Compute the body once so we know whether it's a real implementation
    # or a stub — used by both the rule file and the test file.
    if cls == "HAS_IMPLEMENTATION":
        is_implemented = True
        body_content = None  # not needed — rule file is skipped
    else:
        body_content, is_implemented = render_rule_body(data)

    # Manual-rule sentinel: if the current file contains the marker, treat it
    # as a hand-authored override. Stage 2 preserves it; the test file
    # template assumes the rule is implemented.
    manual_sentinel = "# MANUAL: do not regenerate"
    if rule_path.exists() and manual_sentinel in rule_path.read_text():
        report["rule_skipped"] = "manual override preserved"
        is_implemented = True
    elif write_rule:
        if cls == "HAS_IMPLEMENTATION":
            report["rule_skipped"] = "existing implementation preserved"
        else:
            content = render_header(data) + body_content
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_text(content)
            report["rule_written"] = True

    # Test file — protect existing hand-authored tests unless --overwrite-tests
    if write_test:
        if test_path.exists() and not overwrite_tests:
            report["test_skipped"] = "existing test file preserved"
        else:
            content = render_test_file(data, is_implemented)
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(content)
            report["test_written"] = True

    return report


def load_intermediate_yamls(intermediate_dir: Path) -> list[dict]:
    rules = []
    for f in sorted(intermediate_dir.glob("rule_*.yaml")):
        rules.append(yaml.safe_load(f.read_text()))
    return rules


# ──────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="Write to /tmp/usdm4_stage2_{lib,tests} instead of real paths.")
    ap.add_argument("--only", default="",
                    help="Comma-separated DDF ids to process.")
    ap.add_argument("--no-rules", action="store_true", help="Skip rule file emission.")
    ap.add_argument("--no-tests", action="store_true", help="Skip test file emission.")
    ap.add_argument("--overwrite-tests", action="store_true",
                    help="Overwrite existing test files. Default: preserve them "
                         "(existing tests are often hand-authored with real fixtures).")
    args = ap.parse_args()

    if args.dry_run:
        rule_dir = Path("/tmp/usdm4_stage2_lib")
        test_dir = Path("/tmp/usdm4_stage2_tests")
    else:
        rule_dir = LIBRARY_DIR
        test_dir = TESTS_DIR

    only = {s.strip().upper() for s in args.only.split(",") if s.strip()}

    rules = load_intermediate_yamls(INTERMEDIATE_DIR)
    if only:
        rules = [r for r in rules if r.get("id", "").upper() in only]

    print(f"Intermediate dir: {INTERMEDIATE_DIR}", file=sys.stderr)
    print(f"Rule output:      {rule_dir}", file=sys.stderr)
    print(f"Test output:      {test_dir}", file=sys.stderr)
    print(f"Processing:       {len(rules)} rule(s)", file=sys.stderr)
    print()

    counter: Counter = Counter()
    tests_skipped = 0
    for rule in rules:
        r = emit_rule_and_test(
            rule, rule_dir, test_dir,
            write_rule=not args.no_rules,
            write_test=not args.no_tests,
            overwrite_tests=args.overwrite_tests,
        )
        counter[r["classification"]] += 1
        if r.get("test_skipped"):
            tests_skipped += 1

    print("\n=== Summary by classification ===")
    for cls, n in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])):
        note = "(rule skipped — existing impl preserved)" if cls == "HAS_IMPLEMENTATION" else ""
        print(f"  {n:4d}  {cls:30s}  {note}")
    if tests_skipped:
        print(f"\n  {tests_skipped} test file(s) preserved (already exist; use --overwrite-tests to replace)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
