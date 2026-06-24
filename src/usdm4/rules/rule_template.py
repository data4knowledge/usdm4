from simple_error_log.error_location import ErrorLocation
from simple_error_log.errors import Errors

from usdm4.ct.cdisc.library import Library as CTLibrary


class ValidationLocation(ErrorLocation):
    def __init__(
        self, rule: str, rule_text: str, klass: str, attribute: str, path: str
    ):
        self.rule = rule
        self.rule_text = rule_text
        self.klass = klass
        self.attribute = attribute
        self.path = path

    def to_dict(self):
        return {
            "rule": self.rule,
            "rule_text": self.rule_text,
            "klass": self.klass,
            "attribute": self.attribute,
            "path": self.path,
        }

    @classmethod
    def headers(self):
        return ["rule", "rule_text", "klass", "attribute", "path"]

    def __str__(self):
        return f"{self.rule} [{self.rule_text}]: {self.klass}.{self.attribute} at {self.path}"


class RuleTemplate:
    """
    Base class for rule templates
    """

    ERROR = Errors.ERROR
    WARNING = Errors.WARNING

    class CTException(Exception):
        pass

    def __init__(self, rule: str, level: int, rule_text: str):
        self._errors = Errors()
        self._rule = rule
        self._level = level
        self._rule_text = rule_text

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("rule is not implemented")

    def errors(self) -> Errors:
        return self._errors

    def _add_failure(self, message: str, klass: str, attribute: str, path: str):
        location = ValidationLocation(
            self._rule, self._rule_text, klass, attribute, path
        )
        self._errors.add(message, location, self._rule, self._level)

    def _result(self) -> bool:
        return self._errors.count() == 0

    def _ct_check(self, config: dict, klass: str, attribute: str) -> bool:
        """Validate that every ``klass.attribute`` value conforms to its codelist.

        Resolves the codelist via ``ct.klass_and_attribute`` (a None return
        → :class:`CTException`, which is the "rule registered against an
        unmapped attribute" config flaw), then delegates the per-value
        match to :meth:`Library.find_in_terms` — the single matching
        primitive that all CT-checking rules use. (``find_in_codelist``
        uses the same primitive after resolving a codelist_id.) Both
        entry points share matching semantics so there's no drift.

        Behaviour on empty terms: the resolved codelist with no terms is
        a config flaw, same shape as "codelist not loaded". Raise
        :class:`CTException` (the engine surfaces it as a per-rule
        EXCEPTION outcome). See ``feedback_missing_codelist_must_raise``.
        """
        data = config["data"]
        ct = config["ct"]
        codelist = ct.klass_and_attribute(klass, attribute)
        if codelist is None:
            raise self.CTException(
                f"Failed to find code list for '{klass}' and '{attribute}'"
            )
        terms = codelist.get("terms") or []
        if not terms:
            raise self.CTException(
                f"Codelist for '{klass}.{attribute}' is loaded but has no terms"
            )
        # Use the shared matching primitive directly with the resolved
        # terms — no need to round-trip through find_in_codelist (which
        # would re-resolve the codelist_id we already have).
        for instance in data.instances_by_klass(klass):
            if attribute not in instance:
                self._add_failure(
                    "Missing attribute",
                    klass,
                    attribute,
                    data.path_by_id(instance["id"]),
                )
                continue
            items = (
                instance[attribute]
                if isinstance(instance[attribute], list)
                else [instance[attribute]]
            )
            for item in items:
                # Skip null / non-dict entries — an optional Code attribute
                # that is absent or set to None is a legitimate empty value,
                # not an "invalid code". Also protects `"code" in item` from
                # TypeError when item isn't iterable.
                if not isinstance(item, dict):
                    continue
                # AliasCode-shaped attributes (blindingSchema, studyPhase,
                # etc.) carry the code/decode on `standardCode`, not
                # directly on the item. Dive into standardCode when
                # present; fall back to the item itself for plain Code.
                target = item
                if "standardCode" in item and isinstance(item["standardCode"], dict):
                    target = item["standardCode"]
                code = target.get("code")
                decode = target.get("decode")
                # Call the matching primitive via the Library class
                # (it's a @staticmethod, so no instance access needed).
                # Going through the class rather than ct lets existing
                # rule unit tests stub `ct` with a plain MagicMock —
                # they don't need to also stub find_in_terms.
                code_term, _ = (
                    CTLibrary.find_in_terms(terms, code, by="concept_id")
                    if code is not None
                    else (None, None)
                )
                decode_term, _ = (
                    CTLibrary.find_in_terms(terms, decode, by="any")
                    if decode is not None
                    else (None, None)
                )
                if code_term is None and decode_term is not None:
                    self._add_failure(
                        f"Invalid code '{code}', the code is not in the codelist",
                        klass,
                        attribute,
                        data.path_by_id(instance["id"]),
                    )
                elif code_term is not None and decode_term is None:
                    self._add_failure(
                        f"Invalid decode '{decode}', the decode is not in the codelist",
                        klass,
                        attribute,
                        data.path_by_id(instance["id"]),
                    )
                elif code_term is None and decode_term is None:
                    self._add_failure(
                        f"Invalid code and decode '{code}' and '{decode}', neither the code and decode are in the codelist",
                        klass,
                        attribute,
                        data.path_by_id(instance["id"]),
                    )
                elif code_term.get("conceptId") != decode_term.get("conceptId"):
                    # Pair mismatch — the code resolves to term A and the
                    # decode resolves to term B. The original index-based
                    # comparison is preserved as a conceptId comparison
                    # because find_in_terms returns the full term dict.
                    self._add_failure(
                        f"Invalid code and decode pair '{code}' and '{decode}', the code and decode do not match",
                        klass,
                        attribute,
                        data.path_by_id(instance["id"]),
                    )
        return self._result()
