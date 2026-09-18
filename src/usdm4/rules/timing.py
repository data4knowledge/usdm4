"""Shared Timing predicates for the rule library.

Timing type is matched on the CDISC **code**, never on a decode string.
C201358 carries submissionValue "Fixed Reference" but preferredTerm
"Fixed Reference Timing Type", and the builder writes `decode` from the
preferred term. Rules that compared `type["decode"] == "Fixed Reference"`
never matched real data — silently dead where the guard was `==`, and
reporting a false positive on every anchor where it was `!=`.

There is deliberately no decode fallback. Codes are stable; preferred terms
drift, and accepting two spellings today means accepting a third after the
next CT release. Every Timing the builder emits carries a code, so data that
lacks one is a defect to fix at source rather than to tolerate here.
"""

FIXED_REFERENCE_CODE = "C201358"


def is_fixed_reference(timing: dict) -> bool:
    """True when a Timing is an anchor (Fixed Reference) timing."""
    if not isinstance(timing, dict):
        return False
    type_block = timing.get("type")
    if not isinstance(type_block, dict):
        return False
    return type_block.get("code") == FIXED_REFERENCE_CODE
