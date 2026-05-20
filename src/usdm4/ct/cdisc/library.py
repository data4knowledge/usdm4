import os
from usdm4.ct.cdisc.library_api import LibraryAPI
from usdm4.ct.cdisc.config.config import Config
from usdm4.ct.cdisc.missing.missing import Missing
from usdm4.ct.cdisc.library_cache.library_cache import LibraryCache


class ConfigurationError(Exception):
    """Raised when a missing-CT YAML entry violates a loader constraint.

    Examples: wrong shape for the file it's in, extension targeting a
    codelist that isn't loaded, extension targeting a non-extensible
    codelist, whole-codelist declaration whose conceptId is already
    loaded. These are config-level mistakes, not user-facing findings;
    they should surface as startup errors that block the Library from
    coming up with a half-loaded state.
    """


class Library:
    """
    A class to manage CDISC controlled terminology (CT) data.

    This class handles loading, caching, and accessing CDISC controlled terminology,
    including code lists and their associated terms. It can load data from a local
    cache file or fetch it from the CDISC API when needed.
    """

    BASE_PATH = "ct/cdisc"
    USDM = "usdm"
    ALL = "all"

    def __init__(self, root_path: str, type: str = USDM):
        self.system = "http://www.cdisc.org"
        self.version = "2023-12-15"  # Default version.
        self.root_path = root_path
        self._type = (
            type.lower() if type.lower() in [self.USDM, self.ALL] else self.USDM
        )

        self._config = Config(
            os.path.join(self.root_path, self.BASE_PATH, "config")
        )  # Configuration for required code lists and mappings
        self._missing = Missing(
            os.path.join(self.root_path, self.BASE_PATH, "missing")
        )  # Handler for missing/additional code lists
        self._api = LibraryAPI(
            self._config.required_packages()
        )  # Interface to CDISC Library API
        self._cache = LibraryCache(
            os.path.join(self.root_path, self.BASE_PATH, "library_cache"),
            f"library_cache_{self._type}.yaml",
        )  # Cache file handler

        # Data structures to store and index controlled terminology
        self._by_code_list = {}  # Maps concept IDs to complete code list data
        self._by_term = {}  # Maps term concept IDs to parent code list IDs
        self._by_submission = {}  # Maps submission values to parent code list IDs
        self._by_pt = {}  # Maps preferred terms to parent code list IDs

    def load(self) -> None:
        if self._cache.exists():
            self._load_ct()  # Load from cache file
        else:
            self._api.refresh()  # Ensure API connection is fresh
            self._get_usdm_ct() if self._usdm() else self._get_all_ct()  # Fetch from API
            self._cache.save(self._by_code_list)  # Cache the results
        self._add_missing_ct()  # Add any additional required terminology

    def klass_and_attribute(self, klass, attribute) -> dict:
        try:
            concept_id = self._config.klass_and_attribute(klass, attribute)
            return self._by_code_list[concept_id]
        except Exception:
            return None

    def klass_and_attribute_value(
        self, klass: str, attribute: str, value: str
    ) -> tuple[dict, str]:
        try:
            concept_id = self._config.klass_and_attribute(klass, attribute)
            code_list = self._by_code_list[concept_id]
            return self._get_item(code_list, value), code_list["source"][
                "effective_date"
            ]
        except Exception:
            return None, None

    def unit(self, value: str) -> dict:
        try:
            code_list = self._by_code_list["C71620"]
            return self._get_item(code_list, value)
        except Exception:
            return None

    def unit_code_list(self) -> dict:
        return self._by_code_list["C71620"]

    def effective_dates(self) -> set[str]:
        """Return the set of CDISC terminology effective dates loaded.

        Each loaded codelist carries ``source.effective_date`` (e.g.
        ``"2026-03-27"``); a single CT cache may span multiple package
        releases when codelists from different terminology versions are
        loaded together. Used by ``DDF00155`` to validate
        ``Code.codeSystemVersion`` without a hand-maintained allowlist.
        """
        dates = set()
        for cl in self._by_code_list.values():
            source = cl.get("source") or {}
            ed = source.get("effective_date")
            if ed:
                dates.add(ed)
        return dates

    def cl_by_term(self, term_code: str) -> dict:
        try:
            concept_ids = self._by_term[term_code]
            return self._by_code_list[concept_ids[0]]
        except Exception:
            return None

    def has_codelist(self, codelist_id: str) -> bool:
        """True if ``codelist_id`` is loaded in the Library.

        Companion to :meth:`is_in_codelist` for rules that need to
        distinguish "codelist not loaded (skip the rule, the CT cache
        is stale)" from "codelist loaded but value not a member
        (emit a finding)". Without this distinction, an absent
        codelist would cause :meth:`is_in_codelist` to return False for
        every value, generating spurious findings.
        """
        return codelist_id in self._by_code_list

    def is_in_codelist(
        self, value: str, codelist_id: str, by: str = "any"
    ) -> bool:
        """True if ``value`` is a member of the codelist identified by ``codelist_id``.

        ``by`` selects the match field:

          - ``"concept_id"`` — case-sensitive match on ``term.conceptId``
          - ``"preferred_term"`` — case-insensitive match on ``term.preferredTerm``
          - ``"submission_value"`` — case-insensitive match on ``term.submissionValue``
          - ``"any"`` (default) — try all three in that order

        This is the single membership predicate that d4k rules and M11
        validator rules should call instead of reaching into
        ``_by_code_list`` directly. Extensions added via
        ``_merge_extension`` and codelists added via
        ``_add_whole_codelist`` are transparently included.
        """
        return self.find_in_codelist(value, codelist_id, by)[0] is not None

    def find_in_codelist(
        self, value: str, codelist_id: str, by: str = "any"
    ) -> tuple[dict, str]:
        """Return ``(term, source_tag)`` or ``(None, None)``.

        ``source_tag`` is ``"cdisc"`` for terms loaded from the CDISC
        Library, or the entry's ``source`` string (e.g. ``"NCIt-M11"``)
        for terms added via ``_merge_extension`` / ``_add_whole_codelist``.
        Callers that need to differentiate (e.g. DDF00229's warning-vs-
        error decision) read this tag; callers that only care about
        membership use :meth:`is_in_codelist`.

        See :meth:`is_in_codelist` for the ``by`` parameter semantics.
        """
        cl = self._by_code_list.get(codelist_id)
        if cl is None:
            return (None, None)
        needle = (value or "").casefold()
        for term in cl.get("terms") or []:
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

    def submission(self, value, cl=None):
        if value in list(self._by_submission.keys()):
            return self._find_in_collection(
                self._by_submission[value], "submissionValue", value, cl
            )
        else:
            return None

    def preferred_term(self, value, cl=None):
        if value in list(self._by_pt.keys()):
            return self._find_in_collection(
                self._by_pt[value], "preferredTerm", value, cl
            )
        else:
            return None

    def _usdm(self) -> bool:
        return self._type == self.USDM

    def _find_in_collection(self, concepts: list, key: str, value: str, cl: str = None):
        if len(concepts) == 0:
            return None
        elif len(concepts) == 1:
            code_list = self._by_code_list[concepts[0]]
            return next(
                (
                    item
                    for item in code_list["terms"]
                    if item[key].upper() == value.upper()
                ),
                None,
            )
        else:
            if cl and cl in concepts:
                code_list = self._by_code_list[cl]
                return next(
                    (
                        item
                        for item in code_list["terms"]
                        if item[key].upper() == value.upper()
                    ),
                    None,
                )
            else:
                return None

    def _get_item(self, code_list, value) -> dict:
        try:
            for field in ["conceptId", "preferredTerm", "submissionValue"]:
                result = next(
                    (
                        item
                        for item in code_list["terms"]
                        if item[field].upper() == value.upper()
                    ),
                    None,
                )
                if result:
                    return result
            return None
        except Exception:
            return None

    def _get_usdm_ct(self) -> None:
        for item in self._config.required_code_lists():
            print(f"[{item}] ", end="", flush=True)
            response = self._api.code_list(item)
            self._by_code_list[response["conceptId"]] = response
            for item in response["terms"]:
                # Index each term by its various identifiers
                self._check_in_and_add(
                    self._by_term, item["conceptId"], response["conceptId"]
                )
                self._check_in_and_add(
                    self._by_submission, item["submissionValue"], response["conceptId"]
                )
                self._check_in_and_add(
                    self._by_pt, item["preferredTerm"], response["conceptId"]
                )

    def _get_all_ct(self) -> None:
        for package in self._api.all_code_lists():
            length = len(package["code_lists"])
            print(f"\n\nPackage: {package}: {length}\n")
            for index, code_list in enumerate(package["code_lists"]):
                response = self._api.package_code_list(
                    package["package"], package["effective_date"], code_list
                )
                print(f"[{index}]", end="", flush=True) if index % 10 == 0 else print(
                    "#", end="", flush=True
                )
                self._by_code_list[response["conceptId"]] = response
                for item in response["terms"]:
                    # Index each term by its various identifiers
                    self._check_in_and_add(
                        self._by_term, item["conceptId"], response["conceptId"]
                    )
                    self._check_in_and_add(
                        self._by_submission,
                        item["submissionValue"],
                        response["conceptId"],
                    )
                    self._check_in_and_add(
                        self._by_pt, item["preferredTerm"], response["conceptId"]
                    )

    def _load_ct(self) -> None:
        self._by_code_list = self._cache.read()
        for c_code, entry in self._by_code_list.items():
            for item in entry["terms"]:
                # Rebuild indexes from cached data
                self._check_in_and_add(self._by_term, item["conceptId"], c_code)
                self._check_in_and_add(
                    self._by_submission, item["submissionValue"], c_code
                )
                self._check_in_and_add(self._by_pt, item["preferredTerm"], c_code)

    def _add_missing_ct(self) -> None:
        """Load entries from missing_ct.yaml and m11_codelists.yaml.

        Dispatches on shape (``extends:`` vs ``codelist:``) and enforces
        the per-file invariant: extensions only in ``missing_ct.yaml``,
        whole codelists only in ``m11_codelists.yaml``. Wrong-file
        entries raise :class:`ConfigurationError` so the mistake is
        surfaced at startup rather than silently mis-handled.
        """
        for entry, source_file in self._missing.code_lists():
            if source_file == "missing_ct.yaml":
                if "extends" not in entry or "codelist" in entry:
                    raise ConfigurationError(
                        f"missing_ct.yaml entries must use the 'extends:' shape; "
                        f"got keys {sorted(entry)}"
                    )
                self._merge_extension(entry)
            elif source_file == "m11_codelists.yaml":
                if "codelist" not in entry or "extends" in entry:
                    raise ConfigurationError(
                        f"m11_codelists.yaml entries must use the 'codelist:' shape; "
                        f"got keys {sorted(entry)}"
                    )
                self._add_whole_codelist(entry)
            else:
                raise ConfigurationError(
                    f"Unknown missing-CT source file {source_file!r}"
                )

    def _merge_extension(self, entry: dict) -> None:
        """Add the entry's terms to an already-loaded extensible codelist.

        Raises :class:`ConfigurationError` if the target codelist isn't
        loaded yet (load order should make this impossible — extensions
        are processed after the CDISC cache) or if the target is marked
        ``extensible: false``. Each merged term is stamped with the
        entry's ``source`` tag so the membership predicate can
        distinguish CDISC-published terms from extensions when callers
        need provenance (e.g. DDF00229's warning vs error decision).
        """
        target_id = entry["extends"]
        target = self._by_code_list.get(target_id)
        if target is None:
            raise ConfigurationError(
                f"Extension in missing_ct.yaml targets codelist {target_id!r} "
                f"which is not loaded from the CDISC cache"
            )
        if str(target.get("extensible", "")).lower() != "true":
            raise ConfigurationError(
                f"Cannot extend non-extensible codelist {target_id!r}"
            )
        source_tag = entry.get("source") or "extension"
        for term in entry.get("terms") or []:
            term_with_source = {**term, "source": source_tag}
            target["terms"].append(term_with_source)
            self._check_in_and_add(
                self._by_term, term["conceptId"], target_id
            )
            self._check_in_and_add(
                self._by_submission, term.get("submissionValue", ""), target_id
            )
            self._check_in_and_add(
                self._by_pt, term.get("preferredTerm", ""), target_id
            )

    def _add_whole_codelist(self, entry: dict) -> None:
        """Add a whole new codelist (e.g. M11 C217045) to the Library.

        Used for codelists that the CDISC Library API does not serve.
        Raises :class:`ConfigurationError` if the codelist's conceptId
        is already loaded — duplicate codelist declarations are a
        mistake; use ``extends:`` to add terms to an existing one.
        Each term is stamped with the entry's ``source`` tag.
        """
        codelist_id = entry["codelist"]
        if codelist_id in self._by_code_list:
            raise ConfigurationError(
                f"Codelist {codelist_id!r} declared in m11_codelists.yaml is "
                f"already loaded — use 'extends:' to add terms to an existing codelist"
            )
        source_tag = entry.get("source") or "external"
        terms = [{**t, "source": source_tag} for t in entry.get("terms") or []]
        self._by_code_list[codelist_id] = {
            "conceptId": codelist_id,
            "preferredTerm": entry.get("preferredTerm", ""),
            "definition": entry.get("definition", ""),
            "extensible": entry.get("extensible", False),
            "submissionValue": entry.get("submissionValue", ""),
            "synonyms": entry.get("synonyms", []) or [],
            "source": {
                "effective_date": entry.get("effective_date", ""),
                "package": source_tag,
            },
            "terms": terms,
        }
        for term in terms:
            self._check_in_and_add(
                self._by_term, term["conceptId"], codelist_id
            )
            self._check_in_and_add(
                self._by_submission, term.get("submissionValue", ""), codelist_id
            )
            self._check_in_and_add(
                self._by_pt, term.get("preferredTerm", ""), codelist_id
            )

    def _check_in_and_add(self, collection: dict, id: str, item: str) -> None:
        if id not in collection:
            collection[id] = []
        collection[id].append(item)
