"""Adapter: protocol_corpus ground_truth content -> AssemblerInput dict.

The corpus extraction pipeline emits content blocks shaped *almost* like
``AssemblerInput`` but with two known divergences plus a handful of small
ones. This module is the localised bridge so the eval harness and any
integration tests can use real corpus data without each caller re-doing the
same workarounds.

Long-term, USDM4 itself should accept the corpus shape directly (especially
for SoA) — see ``docs/assembler_validation_findings.md``. Until then, every
transform here corresponds to a tracked finding.

Transforms applied:

  * ``soa`` in the retired ``TimelineInput`` shape (parallel epochs / visits /
    timepoints / windows lists with caller-parsed numbers) -> a list of
    ``ScheduleTimelineInput`` (issue 63), one per table, every table kept.
    The conversion is mechanical — the rules of
    ``docs/timeline_assembler_plan.md`` 63.5 — and exists only because the
    corpus still drafts the old shape; a table already in the new shape
    (it has ``columns``) passes through untouched.

  * ``roles`` keys with hyphens (``co-sponsor``) are normalised to
    underscores (``co_sponsor``) to line up with
    ``IdentificationAssembler.ROLE_ORGS`` keys.

  * Any ``role`` key in the corpus (``sponsor``, ``co_sponsor``, ``cro``,
    ``investigator``, ...) that is NOT in ``IdentificationAssembler.ROLE_ORGS``
    is dropped with a warning recorded on the returned report. We don't
    silently invent role mappings in the adapter — that belongs in the
    assembler.

This module deliberately does NOT:

  * Fill in defaults that ``AssemblerInput.model_validate`` would inject
    on its own (legalAddress=None, other.sponsor_signatory=None, etc.).
    The assembler's failure to use those defaults is a separate finding;
    fixing it here would mask the bug. Instead, the eval harness can be
    configured (via the ``run_validated_dict`` flag in ``adapt``) to
    forward the validated/dumped dict, which is essentially the one-line
    assembler fix in flight.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from usdm4.assembler.identification_assembler import IdentificationAssembler
from usdm4.assembler.schema import AssemblerInput


@dataclass
class AdapterReport:
    """What the adapter changed for one protocol — surfaces silent transforms."""

    soa_timelines_converted: int = 0
    role_keys_normalised: list[tuple[str, str]] = field(default_factory=list)
    role_keys_dropped: list[str] = field(default_factory=list)
    non_standard_type_remapped: list[str] = field(default_factory=list)
    enrollment_defaulted: bool = False
    placeholder_labels: list[str] = field(default_factory=list)
    pydantic_defaults_injected: bool = False


_SOA_UNITS = ("day", "week", "month", "year", "hour", "minute")


def _singular(unit) -> str:
    unit = (unit or "").strip().lower()
    return unit[:-1] if unit.endswith("s") else unit


def _as_int(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _header_value(text, pattern) -> dict | None:
    text = text or ""
    if not text.strip() and not (pattern or "").strip():
        return None
    return {"text": text, "pattern": pattern}


def timeline_input_to_schedule(table: dict) -> dict:
    """One retired ``TimelineInput`` table -> one ``ScheduleTimelineInput``.

    Mechanical, no judgement (plan 63.5): one column per old timepoint
    (``c1``, ``c2`` ...); epoch and visit text as ``{text, pattern: text}``,
    blank -> null; timing ``{text, pattern: "<Unit> <value>"}`` when the old
    value is an integer and its unit is in the grammar, else text only, and a
    blank text with a zero value (a placeholder column) -> null; window ->
    pattern ``-b..+a <units>``, text the old label (blank for a zero window);
    activities flattened, children after their parent with ``parent`` set,
    visit indexes -> cells (``X``) with their markers; conditions ->
    footnotes; ``main_soa`` or no type -> ``main``, other tables ->
    ``profile`` when they carried a ``table_family``, else ``unclassified``.
    """
    table_type = table.get("table_type") or "main_soa"
    if table_type == "main_soa":
        timeline_type = "main"
    elif table.get("table_family"):
        timeline_type = "profile"
    else:
        timeline_type = "unclassified"

    def items(block: str) -> list:
        return (table.get(block) or {}).get("items") or []

    epochs, visits, windows = items("epochs"), items("visits"), items("windows")
    columns = []
    for i, timepoint in enumerate(items("timepoints")):
        epoch = epochs[i].get("text", "") if i < len(epochs) else ""
        visit = visits[i] if i < len(visits) else {"text": "", "references": []}
        value = _as_int(timepoint.get("value"))
        unit = _singular(timepoint.get("unit"))
        text = timepoint.get("text") or ""
        pattern = (
            f"{unit.capitalize()} {value}"
            if value is not None and unit in _SOA_UNITS
            else None
        )
        if not text.strip() and not value:
            pattern = None
        column = {
            "id": f"c{i + 1}",
            "epoch": _header_value(epoch, epoch.strip() or None),
            "visit": _header_value(
                visit.get("text"), (visit.get("text") or "").strip() or None
            ),
            "timing": _header_value(text, pattern),
            "markers": list(visit.get("references") or []),
        }
        if i < len(windows):
            w = windows[i]
            before, after, w_unit = (
                w.get("before", 0),
                w.get("after", 0),
                w.get("unit", "day"),
            )
            column["window"] = {
                "text": ""
                if before == 0 and after == 0
                else f"-{before}..+{after} {w_unit}",
                "pattern": f"-{abs(before)}..+{abs(after)} {_singular(w_unit)}s",
            }
        columns.append(column)

    def row(item: dict, parent: str | None = None) -> dict:
        return {
            "name": item["name"],
            "parent": parent,
            "markers": list(item.get("references") or []),
            "bcs": list(((item.get("actions") or {}).get("bcs")) or []),
            "cells": [
                {
                    "column": f"c{visit['index'] + 1}",
                    "text": "X",
                    "markers": list(visit.get("references") or []),
                }
                for visit in item.get("visits") or []
            ],
        }

    activities = []
    for item in items("activities"):
        activities.append(row(item))
        for child in item.get("children") or []:
            activities.append(row(child, item["name"]))

    return {
        "type": timeline_type,
        "title": table.get("table_title"),
        "description": table.get("table_description"),
        "classification": {
            "orientation": table.get("table_orientation"),
            "unit": table.get("table_unit"),
            "placement": table.get("table_placement"),
        },
        "columns": columns,
        "activities": activities,
        "footnotes": [
            {"marker": c.get("reference") or "", "text": c.get("text", "")}
            for c in items("conditions")
        ],
    }


def _adapt_soa(soa, report: AdapterReport):
    if soa is None:
        return None
    tables = soa if isinstance(soa, list) else [soa]
    if not tables:
        return None
    out = []
    for table in tables:
        if isinstance(table, dict) and "columns" in table:
            out.append(copy.deepcopy(table))
        else:
            out.append(timeline_input_to_schedule(table))
            report.soa_timelines_converted += 1
    return out


def _adapt_non_standard_orgs(identifiers, report: AdapterReport):
    """Bridge the corpus's overload of ``non_standard.type`` to USDM4 schema.

    The corpus emits ``non_standard.type = "sponsor"`` (using ``type`` to mean
    *what role this org plays*). The USDM4 schema's ``NonStandardOrganization``
    splits that into two fields: ``type`` is the org kind (``pharma``,
    ``cro``, ``academic``, ...) and ``role`` is the role label.

    The corpus extractor should be updated to emit the schema-correct shape.
    Until then, when ``type`` isn't a recognised ORG_CODES key, treat it as a
    role hint: move it to ``role`` (unless ``role`` is already set) and
    default ``type`` to ``pharma``.
    """
    if not identifiers:
        return
    valid_types = set(IdentificationAssembler.ORG_CODES.keys())
    for ident in identifiers:
        if not isinstance(ident, dict):
            continue
        scope = ident.get("scope") or {}
        ns = scope.get("non_standard")
        if not isinstance(ns, dict):
            continue
        ns_type = ns.get("type")
        if ns_type and ns_type not in valid_types:
            if not ns.get("role"):
                ns["role"] = ns_type
            ns["type"] = "pharma"
            report.non_standard_type_remapped.append(ns_type)


def _adapt_roles(roles, report: AdapterReport):
    if not roles:
        return roles
    valid_keys = set(IdentificationAssembler.ROLE_ORGS.keys())
    out = {}
    for key, value in roles.items():
        normalised = key.replace("-", "_")
        if normalised != key:
            report.role_keys_normalised.append((key, normalised))
        if normalised not in valid_keys:
            report.role_keys_dropped.append(key)
            continue
        out[normalised] = value
    return out


def adapt(
    content: dict, *, inject_pydantic_defaults: bool = True
) -> tuple[dict, AdapterReport]:
    """Return a copy of ``content`` shaped for ``AssemblerInput``.

    Args:
        content: a corpus ``unvalidated.content`` block.
        inject_pydantic_defaults: when True, round-trip through
            ``AssemblerInput.model_validate(...).model_dump(by_alias=False)``
            so all schema-declared defaults (``other.sponsor_signatory=None``,
            ``non_standard.legalAddress=None``, ``roles[*].address=None``,
            etc.) are present in the dict. The current ``Assembler.execute``
            forwards the *original* dict and accesses these keys
            unconditionally — so unless this flag is True the assembler
            crashes on real corpus data. The flag is here so harness callers
            can compare "with defaults" vs "without" and quantify the
            assembler's missing defensive behaviour.

    Returns:
        (adapted_content, report). ``adapted_content`` is a deep copy with
        the transforms above applied. ``report`` records what changed so
        the eval harness can attribute findings correctly.
    """
    out = copy.deepcopy(content)
    report = AdapterReport()

    if "soa" in out:
        out["soa"] = _adapt_soa(out["soa"], report)

    ident = out.get("identification") or {}
    if "roles" in ident:
        ident["roles"] = _adapt_roles(ident["roles"], report)
    _adapt_non_standard_orgs(ident.get("identifiers"), report)

    # Default enrollment to a zero-persons quantity when the corpus didn't
    # extract enrollment data. Belt-and-braces alongside the USDM4 truthy
    # check in amendments_assembler — corpus protocols never have enrollment
    # so we always emit a non-None enrollment block here.
    amendments = out.get("amendments") or {}
    if amendments.get("enrollment") is None:
        amendments["enrollment"] = {"value": 0, "unit": ""}
        out["amendments"] = amendments
        report.enrollment_defaulted = True

    # USDM4 API models constrain ``name`` to ``min_length=1``. The corpus
    # extractors emit empty ``label`` strings for fields that haven't been
    # populated yet, and the assembler derives both ``name`` and ``label``
    # from the corpus's ``label`` (see study_design_assembler:130 and
    # population_assembler:92). Substitute placeholders so Pydantic doesn't
    # reject the assembled object — surfaces in the report so the missing
    # corpus data isn't lost.
    sd = out.get("study_design") or {}
    if not sd.get("label"):
        sd["label"] = "STUDY-DESIGN"
        out["study_design"] = sd
        report.placeholder_labels.append("study_design")
    pop = out.get("population") or {}
    if not pop.get("label"):
        pop["label"] = "POPULATION"
        out["population"] = pop
        report.placeholder_labels.append("population")

    if inject_pydantic_defaults:
        # The Assembler validates the dict but then uses the *original*
        # dict, throwing away Pydantic-injected defaults. Do the round
        # trip ourselves so the assembler sees a fully-defaulted shape.
        # If validation fails, fall through to the raw dict — the harness
        # will then catch the schema rejection in its usual code path.
        try:
            out = AssemblerInput.model_validate(out).model_dump(by_alias=False)
            report.pydantic_defaults_injected = True
        except Exception:
            pass

    return out, report
