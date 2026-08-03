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

  * ``soa: [main, sub1, sub2, ...]`` (list) -> ``soa: <main>`` (single
    TimelineInput) for compatibility with today's ``AssemblerInput.soa: TimelineInput | None``.
    The first list element is taken as the main timeline; sub-timelines
    are dropped (the assembler can't carry them yet).

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

    soa_list_collapsed: bool = False
    soa_subtimelines_dropped: int = 0
    role_keys_normalised: list[tuple[str, str]] = field(default_factory=list)
    role_keys_dropped: list[str] = field(default_factory=list)
    non_standard_type_remapped: list[str] = field(default_factory=list)
    enrollment_defaulted: bool = False
    placeholder_labels: list[str] = field(default_factory=list)
    pydantic_defaults_injected: bool = False


def _adapt_soa(soa, report: AdapterReport):
    if soa is None:
        return None
    if isinstance(soa, list):
        report.soa_list_collapsed = True
        if not soa:
            return None
        # Pick the main timeline if the entries are tagged, else first entry.
        main_idx = 0
        for i, entry in enumerate(soa):
            if isinstance(entry, dict) and entry.get("table_type") == "main_soa":
                main_idx = i
                break
        report.soa_subtimelines_dropped = max(0, len(soa) - 1)
        main = copy.deepcopy(soa[main_idx])
        # Strip non-AssemblerInput keys the corpus adds (table_type etc.).
        if isinstance(main, dict):
            main.pop("table_type", None)
        return main
    return soa


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
