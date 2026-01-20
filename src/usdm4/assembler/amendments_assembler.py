from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.assembler.encoder import Encoder
from usdm4.builder.builder import Builder
from usdm4.api.quantity_range import Quantity
from usdm4.api.geographic_scope import GeographicScope
from usdm4.api.subject_enrollment import SubjectEnrollment
from usdm4.api.study_amendment_reason import StudyAmendmentReason
from usdm4.api.study_amendment import StudyAmendment
from usdm4.api.code import Code


class AmendmentsAssembler(BaseAssembler):
    MODULE = "usdm4.assembler.amendments_assembler.AmenementsAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        super().__init__(builder, errors)
        self._encoder = Encoder(builder, errors)
        self.clear()

    def clear(self):
        self._amendment = None

    def execute(self, data: dict) -> None:
        try:
            if data:
                self._amendment = self._create_amendment(data)
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception("Failed during creation of amendments", e, location)

    @property
    def amendment(self) -> StudyAmendment:
        return self._amendment

    def _create_amendment(self, data: dict) -> StudyAmendment:
        try:
            self._errors.info(f"Amendment assembler source data {data}")
            reason = {}
            for k, item in data["reasons"].items():
                reason[k] = self._builder.create(
                    StudyAmendmentReason, self._encoder.amendment_reason(item)
                )
            impact = data["impact"]["safety"] or data["impact"]["reliability"]
            params = {
                "name": "AMENDMENT 1",
                "number": data["identifier"],
                "summary": data["summary"],
                "substantialImpact": impact,
                "primaryReason": reason["primary"],
                "secondaryReasons": [reason["secondary"]],
                "enrollments": [self._create_enrollment(data)],
                "geographicScopes": self._create_scopes(data),
            }
            return self._builder.create(StudyAmendment, params)
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception("Failed during creation of amendments", e, location)
            return None

    def _create_enrollment(self, data: dict):
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
                    Quantity, {"value": data["enrollment"]["value"], "unit": unit_alias}
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
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception("Failed during creation of enrollments", e, location)
            return None

    def _create_scopes(self, data: dict) -> list[GeographicScope]:
        results = []
        if "scope" in data:
            if data["scope"]:
                text: str = data["scope"].strip()
                text_upper = text.upper()
                if text_upper.startswith("NOT APPLICABLE"):
                    self._global_scope(results)
                elif text_upper.startswith("GLOBAL"):
                    self._global_scope(results)
                elif text_upper.startswith("NOT GLOBAL") or text_upper.startswith(
                    "LOCAL"
                ):
                    identifier = (
                        text[10:] if text_upper.startswith("NOT GLOBAL") else text[5:]
                    )
                    parts = identifier.split(",")
                    for part in parts:
                        text = part.strip()
                        code, decode = self._builder.iso3166_library.code_or_decode(
                            text
                        )
                        if code:
                            country_code = self._encoder.geographic_scope("COUNTRY")
                            self._create_scope(results, country_code, code, decode)
                        else:
                            code, decode = self._builder.iso3166_library.region_code(
                                text
                            )
                            if code:
                                region_code = self._encoder.geographic_scope("REGION")
                                self._create_scope(results, region_code, code, decode)
                            else:
                                self._errors.error(
                                    f"Failed to set scope for '{part}' from '{data['scope']}', could be a site identifier (not handled currently)",
                                    KlassMethodLocation(self.MODULE, "_create_scopes"),
                                )
                else:
                    self._global_scope(results)
                    self._errors.error(
                        f"Failed to decode scope '{data['scope']}'",
                        KlassMethodLocation(self.MODULE, "_create_scopes"),
                    )
            else:
                self._global_scope(results)
                self._errors.error(
                    "Empty scope found",
                    KlassMethodLocation(self.MODULE, "_create_scopes"),
                )
        else:
            self._global_scope(results)
            self._errors.error(
                "No scope data found",
                KlassMethodLocation(self.MODULE, "_create_scopes"),
            )
        return results

    def _global_scope(self, results: list[GeographicScope]) -> None:
        global_code = self._encoder.geographic_scope("GLOBAL")
        self._create_scope(results, global_code)

    def _create_scope(
        self,
        results: list[GeographicScope],
        type: Code,
        code: str = None,
        decode: str = None,
    ) -> None:
        alias_code = None
        if code and decode:
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
