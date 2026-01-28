"""
Assembler for creating StudyAmendment objects from input data.

This module processes amendment data and constructs USDM4-compliant StudyAmendment
objects including reasons, enrollment information, and geographic scopes.
"""

import re
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.assembler.encoder import Encoder
from usdm4.assembler.document_assembler import DocumentAssembler
from usdm4.builder.builder import Builder
from usdm4.api.quantity_range import Quantity
from usdm4.api.geographic_scope import GeographicScope
from usdm4.api.subject_enrollment import SubjectEnrollment
from usdm4.api.study_amendment_reason import StudyAmendmentReason
from usdm4.api.study_amendment import StudyAmendment
from usdm4.api.study_amendment_impact import StudyAmendmentImpact
from usdm4.api.study_change import StudyChange
from usdm4.api.document_content_reference import DocumentContentReference
from usdm4.api.code import Code
from usdm4.api.narrative_content import NarrativeContent


class AmendmentsAssembler(BaseAssembler):
    """
    Assembler that creates StudyAmendment objects from structured input data.

    Handles the creation of amendments including their reasons, enrollment data,
    and geographic scope information. Supports global, country-specific, and
    region-specific scopes.
    """

    MODULE = "usdm4.assembler.amendments_assembler.AmenementsAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        """
        Initialize the AmendmentsAssembler.

        Args:
            builder: The Builder instance for creating USDM4 objects.
            errors: The Errors instance for logging errors and information.
        """
        super().__init__(builder, errors)
        self._encoder = Encoder(builder, errors)
        self.clear()

    def clear(self):
        """Reset the assembler state by clearing the current amendment."""
        self._amendment = None

    def execute(self, data: dict, document_assembler: DocumentAssembler) -> None:
        """
        Execute the amendment assembly process.

        Processes the input data dictionary and creates a StudyAmendment object.
        Any exceptions during processing are caught and logged.

        Args:
            data: Dictionary containing amendment data with keys like 'identifier',
                  'summary', 'reasons', 'impact', 'enrollment', and 'scope'.
        """
        try:
            self._document_assembler = document_assembler
            if data:
                self._amendment = self._create_amendment(data)
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception("Failed during creation of amendments", e, location)

    @property
    def amendment(self) -> StudyAmendment:
        """
        Get the created StudyAmendment object.

        Returns:
            The StudyAmendment object created by the last execute() call,
            or None if no amendment was created.
        """
        return self._amendment

    def _create_amendment(self, data: dict) -> StudyAmendment:
        """
        Create a StudyAmendment from the provided data.

        Constructs the amendment with primary and secondary reasons, impact flags,
        enrollment information, and geographic scopes.

        Args:
            data: Dictionary containing amendment details.

        Returns:
            A StudyAmendment object, or None if creation fails.
        """
        try:
            self._errors.info(f"Amendment assembler source data {data}")
            reasons = self._create_primary_secondary_reasons(data)
            params = {
                "name": "AMENDMENT 1",
                "number": data["identifier"],
                "summary": data["summary"],
                "impacts": self._create_amendment_impact(data),
                "primaryReason": reasons["primary"],
                "secondaryReasons": [reasons["secondary"]],
                "enrollments": [self._create_enrollment(data)],
                "geographicScopes": self._create_scopes(data),
                "changes": self._create_changes(data),
            }
            return self._builder.create(StudyAmendment, params)
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception("Failed during creation of amendments", e, location)
            return None

    def _create_primary_secondary_reasons(
        self, data: dict
    ) -> dict[str, StudyAmendmentReason]:
        reasons = {}
        for k, item in data["reasons"].items():
            a_reason = self._encoder.amendment_reason(item)
            a_reason["otherReason"] = a_reason.pop("other_reason")
            reasons[k] = self._builder.create(StudyAmendmentReason, a_reason)
        return reasons

    def _create_changes(self, data: dict) -> list[StudyChange]:
        results = []
        for index, item in enumerate(data["changes"]):
            refs = self._extract_section_numer_and_title(item["section"])
            params = {
                "name": f"CHANGE_{index + 1}",
                "summary": item["description"].strip(),
                "rationale": item["rationale"].strip(),
                "changedSections": refs,
            }
            change = self._builder.create(StudyChange, params)
            if change:
                results.append(change)
        return results

    def _extract_section_numer_and_title(self, text) -> list[DocumentContentReference]:
        results = []
        pattern = r"^(?:Section\s+)?(\d+(?:\.\d+)*),?\s*(.*)$"
        for line in text.strip().split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                params = {
                    "sectionNumber": match.group(1),
                    "sectionTitle": match.group(2),
                    "appliesToId": self._document_assembler.document.id,
                }
                ref = self._builder.create(DocumentContentReference, params)
                if ref:
                    results.append(ref)
                    self._errors.info(
                        f"Extracted section ref from '{line}' -> {params}",
                        KlassMethodLocation(
                            self.MODULE, "_extract_section_numer_and_title"
                        ),
                    )
            else:
                self._errors.error(
                    f"Failed to extract section ref from '{line}'",
                    KlassMethodLocation(
                        self.MODULE, "_extract_section_numer_and_title"
                    ),
                )
        return results

    def _create_amendment_impact(self, data: dict) -> list[StudyAmendmentImpact]:
        try:
            results = []
            self._errors.info(
                f"Creating amendment impacts using {data['impact']}",
                KlassMethodLocation(self.MODULE, "_create_amendment_impact"),
            )
            impact = data["impact"]
            s_and_r = impact["safety_and_rights"]
            r_and_r = impact["reliability_and_robustness"]
            # print(f"\nR-R1: {r_and_r}")
            # print(f"R-R2: {r_and_r["reliability"]}")
            self._create_impact(
                results,
                "C215665",
                "Study Subject Safety",
                s_and_r["safety"]["substantial"],
                s_and_r["safety"]["reason"],
            )
            self._create_impact(
                results,
                "C215666",
                "Study Subject Rights",
                s_and_r["rights"]["substantial"],
                s_and_r["rights"]["reason"],
            )
            self._create_impact(
                results,
                "C215667",
                "Study Data Reliability",
                r_and_r["reliability"]["substantial"],
                r_and_r["reliability"]["reason"],
            )
            self._create_impact(
                results,
                "C215668",
                "Study Data Robustness",
                r_and_r["robustness"]["substantial"],
                r_and_r["robustness"]["reason"],
            )
            return results
        except Exception as e:
            self._errors.exception(
                "Failed during creation of amendment impacts",
                e,
                KlassMethodLocation(self.MODULE, "_create_amendment_impact"),
            )
            return []

    def _create_impact(
        self,
        results: list[StudyAmendmentImpact],
        code: str,
        decode: str,
        is_substantial: bool,
        text: str,
    ) -> None:
        type_code = self._builder.cdisc_code(code, decode)
        params = {
            "text": text,
            "isSubstantial": is_substantial,
            "type": type_code,
        }
        item = self._builder.create(StudyAmendmentImpact, params)
        if item:
            results.append(item)

    def _create_enrollment(self, data: dict) -> SubjectEnrollment:
        """
        Create a SubjectEnrollment object from the provided data.

        If enrollment data is present, creates a quantity with the specified value
        and unit (percentage if '%'). Otherwise, creates a default enrollment with
        value 0.

        Args:
            data: Dictionary that may contain an 'enrollment' key with 'value' and 'unit'.

        Returns:
            A SubjectEnrollment object, or None if creation fails.
        """
        try:
            global_code = self._builder.cdisc_code("C68846", "Global")
            params = {
                "type": global_code,
                "code": None,
            }
            geo_scope = self._builder.create(GeographicScope, params)
            if "enrollment" in data:
                unit_alias = None
                if data["enrollment"]["unit"] == "%":
                    unit_code = self._builder.cdisc_code("C25613", "Percentage")
                    unit_alias = (
                        self._builder.alias_code(unit_code) if unit_code else None
                    )
                quantity = self._builder.create(
                    Quantity,
                    {
                        "value": self._to_int(data["enrollment"]["value"]),
                        "unit": unit_alias,
                    },
                )
                params = {
                    "name": "ENROLLMENT",
                    "forGeographicScope": geo_scope,
                    "quantity": quantity,
                }
            else:
                quantity = self._builder.create(Quantity, {"value": 0, "unit": None})
                params = {
                    "name": "ENROLLMENT",
                    "forGeographicScope": geo_scope,
                    "quantity": quantity,
                }
            return self._builder.create(SubjectEnrollment, params)
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "_create_enrollment")
            self._errors.exception("Failed during creation of enrollments", e, location)
            return None

    def _to_int(self, item: str | int) -> int:
        try:
            return item if isinstance(item, int) else int(str(item))
        except Exception as e:
            self._errors.exception(
                f"Failed to convert '{item}' to integer value",
                e,
                KlassMethodLocation(self.MODULE, "_to_int"),
            )
            return 0

    def _create_scopes(self, data: dict) -> list[GeographicScope]:
        """
        Create geographic scopes from the scope data.

        Parses the 'scope' field and creates appropriate GeographicScope objects:
        - "NOT APPLICABLE" or "GLOBAL": Creates a global scope
        - "NOT GLOBAL <countries>" or "LOCAL <countries>": Creates country/region scopes
        - Unrecognized format: Defaults to global scope with an error

        Country codes are looked up in the ISO3166 library. If a code is not found
        as a country, it is checked as a region code.

        Args:
            data: Dictionary that may contain a 'scope' key.

        Returns:
            List of GeographicScope objects.
        """
        results = []
        if "scope" in data and data["scope"]:
            scope = data["scope"]
            # {"global": True, "countries": [], "regions": [], "sites": [], "unknown": []}
            if scope["global"]:
                self._global_scope(results)
            else:
                for part in scope["unknown"]:
                    text = part.strip()
                    if not text:
                        continue
                    # Try to find as a country code first
                    code, decode = self._builder.iso3166_library.code_or_decode(text)
                    if code:
                        country_code = self._encoder.geographic_scope("COUNTRY")
                        self._create_scope(results, country_code, code, decode)
                    else:
                        # If not a country, try as a region code
                        code, decode = self._builder.iso3166_library.region_code(text)
                        if code:
                            region_code = self._encoder.geographic_scope("REGION")
                            self._create_scope(results, region_code, code, decode)
                        else:
                            self._errors.error(
                                f"Failed to set scope for '{part}' from '{data['scope']}', could be a site identifier (not handled currently)",
                                KlassMethodLocation(self.MODULE, "_create_scopes"),
                            )
                for part in scope["countries"]:
                    code, decode = self._builder.iso3166_library.code_or_decode(part)
                    if code:
                        country_code = self._encoder.geographic_scope("COUNTRY")
                        self._create_scope(results, country_code, code, decode)
                for part in scope["regions"]:
                    code, decode = self._builder.iso3166_library.region_code(part)
                    if code:
                        region_code = self._encoder.geographic_scope("REGION")
                        self._create_scope(results, region_code, code, decode)
                for part in scope["sites"]:
                    self._errors.error(
                        f"Failed to set scope for site identifier '{part}' (not handled currently)",
                        KlassMethodLocation(self.MODULE, "_create_scopes"),
                    )
        else:
            # Empty scope string - default to global and log error
            self._global_scope(results)
            self._errors.error(
                "Empty scope found",
                KlassMethodLocation(self.MODULE, "_create_scopes"),
            )
        return results

    def _global_scope(self, results: list[GeographicScope]) -> None:
        """
        Add a global geographic scope to the results list.

        Args:
            results: List to append the global scope to.
        """
        global_code = self._encoder.geographic_scope("GLOBAL")
        self._create_scope(results, global_code)

    def _create_scope(
        self,
        results: list[GeographicScope],
        type: Code,
        code: str = None,
        decode: str = None,
    ) -> None:
        """
        Create a GeographicScope and add it to the results list.

        For country scopes (C25464), looks up the ISO3166 country code.
        For region scopes, looks up the ISO3166 region code.
        Creates an alias code from the standard code if found.

        Args:
            results: List to append the created scope to.
            type: The Code object indicating the scope type (Country, Global, Region).
            code: Optional ISO code string (e.g., 'US', '150').
            decode: Optional human-readable decode for the code.
        """
        alias_code = None
        if code and decode:
            # Look up the standard code based on scope type
            std_code = (
                self._builder.iso3166_code(code)
                if type.code == "C25464"
                else self._builder.iso3166_region_code(code)
            )
            if std_code:
                alias_code = self._builder.alias_code(std_code)
            else:
                self._errors.error(
                    f"Failed to create standard code for '{code}', '{decode}'",
                    KlassMethodLocation(self.MODULE, "_create_scope"),
                )
        gs = self._builder.create(GeographicScope, {"type": type, "code": alias_code})
        if gs:
            self._errors.info(
                f"Created scope of type {type.decode}{f' -> [{code}, {decode}]' if code else ''}",
                KlassMethodLocation(self.MODULE, "_create_scope"),
            )
            results.append(gs)
        else:
            self._errors.error(
                f"Failed to create geographic scope for {type}, {code}, {decode}",
                KlassMethodLocation(self.MODULE, "_create_scope"),
            )
