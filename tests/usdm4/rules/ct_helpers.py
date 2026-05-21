"""Shared CT test helpers for d4k rule unit tests.

A small ``FakeCT`` mirrors the public surface of
:class:`usdm4.ct.cdisc.library.Library` that CT-checking rules consume —
``klass_and_attribute``, ``is_in_codelist`` and ``find_in_codelist``.
Used by ``test_rule_ddf00229.py`` and ``test_rule_ddf00237.py`` (and any
future d4k rule that exercises the predicate API) so the stub stays in
one place and can't drift from the real Library contract.

The behaviour mirrors :class:`Library` precisely:

- ``is_in_codelist`` and ``find_in_codelist`` raise
  :class:`MissingCodelistError` when ``codelist_id`` is unknown OR
  when the codelist is loaded with no terms. Both are config flaws,
  not membership outcomes (see ``feedback_missing_codelist_must_raise``).
- Matching by ``concept_id`` is case-sensitive; matching by
  ``preferred_term`` and ``submission_value`` is case-insensitive
  (casefold). ``"any"`` tries all three in order.
- Extension terms carry a ``source`` tag; the predicate returns it
  alongside the term so callers can distinguish CDISC-loaded terms
  from sanctioned extensions.

The Library equivalent is the authoritative implementation; if the
two ever diverge in semantics, fix this file to match — not the
other way round.
"""

from usdm4.ct.cdisc.library import MissingCodelistError


class FakeCT:
    """In-memory CT stub mirroring the public Library predicate surface.

    Construct with ``{codelist_id: [term_dict, ...]}``. Each term dict
    may carry ``conceptId``, ``preferredTerm``, ``submissionValue`` and
    optionally ``source`` (for extension provenance).

    Optionally pass ``klass_attribute_map`` ({(klass, attribute):
    codelist_id}) so the stub answers :meth:`klass_and_attribute`
    lookups in the same shape ``Library`` does — used by tests that
    exercise :meth:`RuleTemplate._ct_check` and need the rule to
    resolve a codelist from a (klass, attribute) pair.
    """

    def __init__(
        self,
        codelists: dict[str, list[dict]],
        klass_attribute_map: dict[tuple[str, str], str] | None = None,
    ):
        self._codelists = codelists
        self._klass_attribute_map = dict(klass_attribute_map or {})

    def klass_and_attribute(self, klass: str, attribute: str) -> dict | None:
        """Return the codelist dict for ``(klass, attribute)`` or None.

        Mirrors :meth:`Library.klass_and_attribute`: the codelist dict
        carries ``conceptId`` and ``terms`` so callers can either pass
        the terms to :meth:`find_in_terms` directly (as
        :meth:`RuleTemplate._ct_check` does) or re-query by conceptId
        via :meth:`find_in_codelist`.
        """
        codelist_id = self._klass_attribute_map.get((klass, attribute))
        if codelist_id is None:
            return None
        if codelist_id not in self._codelists:
            return None
        return {
            "conceptId": codelist_id,
            "terms": list(self._codelists[codelist_id]),
        }

    def is_in_codelist(
        self, value: str, codelist_id: str, by: str = "any"
    ) -> bool:
        return self.find_in_codelist(value, codelist_id, by)[0] is not None

    def find_in_codelist(
        self, value: str, codelist_id: str, by: str = "any"
    ) -> tuple[dict | None, str | None]:
        if codelist_id not in self._codelists:
            raise MissingCodelistError(
                f"Codelist {codelist_id!r} is not loaded in the CT cache"
            )
        terms = self._codelists[codelist_id]
        if not terms:
            raise MissingCodelistError(
                f"Codelist {codelist_id!r} is loaded but has no terms"
            )
        return self.find_in_terms(terms, value, by)

    @staticmethod
    def find_in_terms(
        terms: list[dict], value: str, by: str = "any"
    ) -> tuple[dict | None, str | None]:
        needle = (value or "").casefold()
        for term in terms:
            if by in ("concept_id", "any") and term.get("conceptId", "") == value:
                return (term, term.get("source") or "cdisc")
            if by in ("preferred_term", "any") and (
                term.get("preferredTerm") or ""
            ).casefold() == needle:
                return (term, term.get("source") or "cdisc")
            if by in ("submission_value", "any") and (
                term.get("submissionValue") or ""
            ).casefold() == needle:
                return (term, term.get("source") or "cdisc")
        return (None, None)
