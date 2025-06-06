from uuid import uuid4
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.api.wrapper import Wrapper
from usdm4.api.code import Code
from usdm4.api.alias_code import AliasCode
from usdm4.api.geographic_scope import GeographicScope
from usdm4.api.governance_date import GovernanceDate
from usdm4.api.organization import Organization
from usdm4.api.study import Study
from usdm4.api.study_definition_document import StudyDefinitionDocument
from usdm4.api.study_definition_document_version import StudyDefinitionDocumentVersion
from usdm4.api.identifier import StudyIdentifier
from usdm4.api.study_title import StudyTitle
from usdm4.api.study_version import StudyVersion
from usdm4.api import __all__ as v4_classes
from usdm4.__version__ import __model_version__, __package_version__
from usdm3.base.id_manager import IdManager
from usdm3.base.api_instance import APIInstance
from usdm3.ct.cdisc.library import Library as CdiscLibrary
from usdm4.ct.iso.iso3166.library import Library as Iso3166Library
from usdm4.ct.iso.iso639.library import Library as Iso639Library
from usdm4.builder.cross_reference import CrossReference


class Builder:
    def __init__(self, root_path: str):
        self._id_manager: IdManager = IdManager(v4_classes)
        self.errors = Errors()
        self.api_instance: APIInstance = APIInstance(self._id_manager)
        self.cdisc_library = CdiscLibrary(root_path)
        self.iso3166_library = Iso3166Library(root_path)
        self.iso639_library = Iso639Library(root_path)
        self.cross_reference = CrossReference()
        self.cdisc_library.load()
        self.iso3166_library.load()
        self.iso639_library.load()
        self._cdisc_code_system = self.cdisc_library.system
        self._cdisc_code_system_version = self.cdisc_library.version

    def create(self, klass, params):
        try:
            object = self.api_instance.create(klass, params)
            if object:
                self.cross_reference.add(object)
            return object
        except Exception as e:
            location = KlassMethodLocation("Builder", "create")
            self.errors.exception(
                f"Failed to create instance of klass '{klass}' with params {params}",
                e,
                location,
            )
            return None

    def minimum(self, title: str, identifier: str, version: str) -> "Wrapper":
        """
        Create a minimum study with the given title, identifier, and version.
        """
        # Clear errors
        self.errors.clear()

        # Define the codes to be used in the study
        english_code = self.iso639_code("en")
        title_type = self.cdisc_code("C207616", "Official Study Title")
        organization_type_code = self.cdisc_code("C70793", "Clinical Study Sponsor")
        doc_status_code = self.cdisc_code("C25425", "Approved")
        protocol_code = self.cdisc_code("C70817", "Protocol")
        global_code = self.cdisc_code("C68846", "Global")
        global_scope = self.create(GeographicScope, {"type": global_code})
        approval_date_code = self.cdisc_code("C132352", "Sponsor Approval Date")

        # Study Title
        study_title = self.create(StudyTitle, {"text": title, "type": title_type})

        # Governance dates
        approval_date = self.create(
            GovernanceDate,
            {
                "name": "D_APPROVE",
                "label": "Design Approval",
                "description": "Design approval date",
                "type": approval_date_code,
                "dateValue": "2006-06-01",
                "geographicScopes": [global_scope],
            },
        )
        # Define the organization and the study identifier
        organization = self.create(
            Organization,
            {
                "name": "Sponsor",
                "type": organization_type_code,
                "identifier": "To be provided",
                "identifierScheme": "To be provided",
                "legalAddress": None,
            },
        )
        study_identifier = self.create(
            StudyIdentifier,
            {"text": identifier, "scopeId": organization.id},
        )

        # Documenta
        study_definition_document_version = self.create(
            StudyDefinitionDocumentVersion,
            {"version": "1", "status": doc_status_code, "dateValues": [approval_date]},
        )
        study_definition_document = self.create(
            StudyDefinitionDocument,
            {
                "name": "PROTOCOL DOCUMENT",
                "label": "Protocol Document",
                "description": "The entire protocol document",
                "language": english_code,
                "type": protocol_code,
                "templateName": "Sponsor",
                "versions": [study_definition_document_version],
            },
        )

        study_version = self.create(
            StudyVersion,
            {
                "versionIdentifier": "1",
                "rationale": "To be provided",
                "titles": [study_title],
                "studyDesigns": [],
                "documentVersionIds": [study_definition_document_version.id],
                "studyIdentifiers": [study_identifier],
                "studyPhase": None,
                "dateValues": [approval_date],
                "amendments": [],
                "organizations": [organization],
            },
        )
        study = self.create(
            Study,
            {
                "id": str(uuid4()),
                "name": "Study",
                "label": title,
                "description": title,
                "versions": [study_version],
                "documentedBy": [study_definition_document],
            },
        )

        # Return the wrapper for the study
        result = self.api_instance.create(
            Wrapper,
            {
                "study": study,
                "usdmVersion": __model_version__,
                "systemName": "Python USDM4 Package",
                "systemVersion": __package_version__,
            },
        )
        return result

    # def decode_phase(self, text) -> AliasCode:
    #     phase_map = [
    #         (
    #             ["0", "PRE-CLINICAL", "PRE CLINICAL"],
    #             {"code": "C54721", "decode": "Phase 0 Trial"},
    #         ),
    #         (["1", "I"], {"code": "C15600", "decode": "Phase I Trial"}),
    #         (["1-2"], {"code": "C15693", "decode": "Phase I/II Trial"}),
    #         (["1/2"], {"code": "C15693", "decode": "Phase I/II Trial"}),
    #         (["1/2/3"], {"code": "C198366", "decode": "Phase I/II/III Trial"}),
    #         (["1/3"], {"code": "C198367", "decode": "Phase I/III Trial"}),
    #         (["1A", "IA"], {"code": "C199990", "decode": "Phase Ia Trial"}),
    #         (["1B", "IB"], {"code": "C199989", "decode": "Phase Ib Trial"}),
    #         (["2", "II"], {"code": "C15601", "decode": "Phase II Trial"}),
    #         (["2-3", "II-III"], {"code": "C15694", "decode": "Phase II/III Trial"}),
    #         (["2A", "IIA"], {"code": "C49686", "decode": "Phase IIa Trial"}),
    #         (["2B", "IIB"], {"code": "C49688", "decode": "Phase IIb Trial"}),
    #         (["3", "III"], {"code": "C15602", "decode": "Phase III Trial"}),
    #         (["3A", "IIIA"], {"code": "C49687", "decode": "Phase IIIa Trial"}),
    #         (["3B", "IIIB"], {"code": "C49689", "decode": "Phase IIIb Trial"}),
    #         (["4", "IV"], {"code": "C15603", "decode": "Phase IV Trial"}),
    #         (["5", "V"], {"code": "C47865", "decode": "Phase V Trial"}),
    #     ]
    #     for tuple in phase_map:
    #         if text in tuple[0]:
    #             entry = tuple[1]
    #             cdisc_phase_code = self.cdisc_code(entry["code"], entry["decode"])
    #             return self.alias_code(cdisc_phase_code)
    #     cdisc_phase_code = self.cdisc_code(
    #         "C48660",
    #         "[Trial Phase] Not Applicable",
    #     )
    #     return self.alias_code(cdisc_phase_code)

    def klass_and_attribute(self, klass: str, attribute: str) -> Code:
        return self.cdisc_library.klass_and_attribute(klass, attribute)

    def cdisc_code(self, code: str, decode: str) -> Code:
        cl = self.cdisc_library.cl_by_term(code)
        version = cl["source"]["effective_date"] if cl else "unknown"
        return self.create(
            Code,
            {
                "code": code,
                "codeSystem": self._cdisc_code_system,
                "codeSystemVersion": version,
                "decode": decode,
            },
        )

    def cdisc_unit_code(self, unit: str) -> Code:
        unit = self.cdisc_library.unit(unit)
        unit_cl = self.cdisc_library.unit_code_list()
        return (
            self.create(
                Code,
                {
                    "code": unit["conceptId"],
                    "codeSystem": self._cdisc_code_system,
                    "codeSystemVersion": unit_cl["source"]["effective_date"],
                    "decode": unit["preferredTerm"],
                },
            )
            if unit
            else None
        )

    def alias_code(self, standard_code: Code) -> AliasCode:
        return self.create(AliasCode, {"standardCode": standard_code})

    def iso3166_code(self, code: str) -> Code:
        return self.create(
            Code,
            {
                "code": code,
                "codeSystem": self.iso3166_library.system,
                "codeSystemVersion": self.iso3166_library.version,
                "decode": self.iso3166_library.decode(code),
            },
        )

    def iso639_code(self, code: str) -> Code:
        return self.create(
            Code,
            {
                "code": code,
                "codeSystem": self.iso639_library.system,
                "codeSystemVersion": self.iso639_library.version,
                "decode": self.iso639_library.decode(code),
            },
        )

    def sponsor(self, sponsor_name: str) -> Organization:
        sponsor_code = self.cdisc_code("C70793", "Clinical Study Sponsor")
        return self.create(
            Organization,
            {
                "name": sponsor_name,
                "label": sponsor_name,
                "type": sponsor_code,
                "identifier": "---------",
                "identifierScheme": "DUNS",
                # "legalAddress": address
            },
        )

    def double_link(self, items, prev_attribute, next_attribute):
        for idx, item in enumerate(items):
            if idx == 0:
                setattr(item, prev_attribute, None)
            else:
                the_id = getattr(items[idx - 1], "id")
                setattr(item, prev_attribute, the_id)
            if idx == len(items) - 1:
                setattr(item, next_attribute, None)
            else:
                the_id = getattr(items[idx + 1], "id")
                setattr(item, next_attribute, the_id)

    def load(self, data: dict):
        self._decompose(data, None, "")

    def _decompose(self, data) -> None:
        if isinstance(data, dict):
            self._add_id(data)
            for key, value in data.items():
                if isinstance(value, dict):
                    self._decompose(value, data)
                elif isinstance(value, list):
                    for index, item in enumerate(value):
                        self._decompose(item, data)

    def _add_id(self, data: dict):
        self._id_manager.add_id(data["instanceType"], data["id"])
