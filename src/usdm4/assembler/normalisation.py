"""Structured trace for value normalisations performed during assembly.

When the encoder coerces a source value to a canonical CT term (e.g.
``Phase III`` → ``Phase 3``), this module appends a typed entry to the
shared ``Errors`` log so downstream validators can surface the deviation
as a finding rather than burying it as free text.

Two record kinds:

- ``coerced`` — the source value differed from the canonical term but a
  mapping was found and applied.
- ``unmapped`` — the source value had no matching entry in the lookup;
  the encoder fell back to a default code or marked the value
  ``Not Applicable``.

Records carry a structured ``extra`` payload (``element``, ``source``,
``normalised``, ``kind``) so consumers don't parse the message string.
The ``error_type`` tag (``M11_NORMALIZATION_RECORD``) is the filter key.
"""

from simple_error_log.errors import Errors
from simple_error_log.error_location import ErrorLocation


# Filter key. Consumers (e.g. the M11 validator in usdm4_protocol) match
# log entries by this exact string. Keep the value stable across versions.
M11_NORMALIZATION_RECORD = "m11_normalization_record"

KIND_COERCED = "coerced"
KIND_UNMAPPED = "unmapped"


def record_normalisation(
    errors: Errors,
    element: str,
    source: str,
    normalised: str,
    kind: str = KIND_COERCED,
    location: ErrorLocation = None,
) -> None:
    """Append a normalisation record to the error log.

    For ``kind="coerced"``, the call is suppressed when ``source`` and
    ``normalised`` are equivalent (case- and whitespace-insensitive) — that
    means no actual normalisation occurred and nothing needs reporting.

    Logged at WARNING so it surfaces in the default error dump. Caller
    chose WARNING (not ERROR) deliberately: the encoder did its job; the
    finding is educational, not blocking.
    """
    if kind == KIND_COERCED and _values_equivalent(source, normalised):
        return
    if kind == KIND_COERCED:
        message = (
            f"M11 normalisation: '{element}' source value '{source}' "
            f"coerced to canonical term '{normalised}'."
        )
    else:
        message = (
            f"M11 normalisation: '{element}' source value '{source}' "
            f"could not be mapped to a canonical term "
            f"(default applied: '{normalised}')."
        )
    errors.warning(
        message,
        location=location,
        error_type=M11_NORMALIZATION_RECORD,
        extra={
            "element": element,
            "source": source,
            "normalised": normalised,
            "kind": kind,
        },
    )


def _values_equivalent(source: str, normalised: str) -> bool:
    """True when the two values are equivalent for normalisation purposes
    (case- and whitespace-insensitive). ``None`` and ``""`` compare equal
    to themselves only."""
    if source is None or normalised is None:
        return source == normalised
    return source.strip().lower() == normalised.strip().lower()
