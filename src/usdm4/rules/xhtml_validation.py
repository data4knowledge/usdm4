"""Shared XHTML validator for the USDM-XHTML 1.0 schema.

Rules DDF00187 (NarrativeContentItem.text) and DDF00247 (syntax template
text across six classes) both need to check that narrative text is valid
per the USDM-XHTML 1.0 schema. The schema is the CDISC-flavoured XHTML
1.1 with `<usdm:ref>` and `<usdm:tag>` extension elements — the same
schema the CDISC CORE engine validates against, bundled at
`src/usdm4/rules/library/schema/xml/` from the CORE cache.

Narrative text in USDM is a fragment (sequence of block elements), not a
complete document. We wrap the fragment in a minimal valid XHTML
document (`html > head > body > fragment`) before parsing so the schema
can validate it.

Two classes of problem are detected and returned uniformly:

  - Parse errors (not well-formed XML) — e.g. "error parsing attribute
    name", unclosed tags, bad entities.
  - Schema violations — e.g. `<p>` direct child of `<ul>` ("Element 'p'
    is not expected, expected is (li)").

Both report with line numbers relative to the wrapped document. The
line offset that the wrapper adds (the wrapper occupies line 1) is
normalised out so the reported lines align with the original text.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List

from lxml import etree


SCHEMA_ENTRY = (
    Path(__file__).parent
    / "library"
    / "schema"
    / "xml"
    / "cdisc-usdm-xhtml-1.0"
    / "usdm-xhtml-1.0.xsd"
)

# Wrapper: valid XHTML document that allows narrative fragments.
# Fragments in USDM can be plain text, inline markup, or block markup —
# sometimes a mix. <body> requires block-only children, which would
# wrongly flag bare text ("foo bar") as a schema violation. <div>
# accepts Flow content (text + inline + block), so the fragment slots
# in regardless of its top-level shape. Parse errors and block-inside-
# inline nesting violations are still caught.
# Kept on a single line so reported line numbers inside the fragment
# match the user's source (our wrapper line 1 → their line 1).
_WRAPPER_OPEN = (
    '<html xmlns="http://www.w3.org/1999/xhtml" '
    'xmlns:usdm="http://www.cdisc.org/ns/usdm/xhtml/v1.0">'
    "<head><title>t</title></head><body><div>"
)
_WRAPPER_CLOSE = "</div></body></html>"


@dataclass(frozen=True)
class XhtmlError:
    line: int | None
    message: str


class XhtmlValidator:
    """Loads the USDM-XHTML 1.0 schema once and validates fragments against it.

    Instantiation is moderately expensive (parses 65 XSD files and builds
    the schema); re-use the same instance across rule invocations via the
    module-level `get_validator()` helper.
    """

    def __init__(self, schema_path: Path | None = None) -> None:
        path = Path(schema_path) if schema_path else SCHEMA_ENTRY
        if not path.is_file():
            raise FileNotFoundError(f"XHTML schema not found at {path}")
        with path.open("rb") as fh:
            schema_doc = etree.parse(fh)
        self._schema = etree.XMLSchema(schema_doc)
        # Line 1 of the wrapped document is the wrapper itself. Subsequent
        # lines come from the fragment, so a fragment line N appears on
        # line N+1 of the wrapped document when the fragment is emitted on
        # its own line. We splice the fragment starting on line 1 after
        # the wrapper's trailing '>' so both schema-error and parse-error
        # line numbers come out close to the original. See validate().

    def validate(self, text: str) -> List[XhtmlError]:
        """Validate a narrative fragment. Return list of errors (empty = OK)."""
        if text is None:
            return []
        if not isinstance(text, str):
            return [XhtmlError(None, f"text is not a string (type={type(text).__name__})")]
        if text.strip() == "":
            return []
        wrapped = _WRAPPER_OPEN + text + _WRAPPER_CLOSE
        try:
            doc = etree.fromstring(wrapped.encode("utf-8"))
        except etree.XMLSyntaxError as exc:
            # lxml reports a synthesised line from the wrapped document;
            # since the wrapper occupies line 1 and the fragment starts on
            # the same line, the line numbers line up 1:1 with the source
            # text.
            return [XhtmlError(exc.lineno, str(exc).split("(", 1)[0].strip())]
        if self._schema.validate(doc):
            return []
        errors: List[XhtmlError] = []
        for err in self._schema.error_log:
            errors.append(XhtmlError(err.line, err.message))
        return errors


# ---------------------------------------------------------------------------
# Module-level lazy singleton — building the schema is expensive; rule
# engines run many rules and may instantiate each several times.
# ---------------------------------------------------------------------------

_singleton: XhtmlValidator | None = None
_singleton_lock = threading.Lock()


def get_validator() -> XhtmlValidator:
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                _singleton = XhtmlValidator()
    return _singleton
