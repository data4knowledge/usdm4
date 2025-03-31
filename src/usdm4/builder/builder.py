from uuid import uuid4
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


class Builder:
    def __init__(self):
        self._id_manager: IdManager = IdManager(v4_classes)
        self.api_instance: APIInstance = APIInstance(self._id_manager)
        self._cdisc_code_system = "cdisc.org"
        self._cdisc_code_system_version = "2023-12-15"

    def minimum(self, title: str, identifier: str, version: str) -> "Wrapper":
        """
        Create a minimum study with the given title, identifier, and version.
        """

        # Define the codes to be used in the study
        english_code = self.api_instance.create(
            Code,
            {
                "code": "en",
                "codeSystem": "ISO 639-1",
                "codeSystemVersion": "2007",
                "decode": "English",
            },
        )
        title_type = self.api_instance.create(
            Code,
            {
                "code": "C207616",
                "codeSystem": self._cdisc_code_system,
                "codeSystemVersion": self._cdisc_code_system_version,
                "decode": "Official Study Title",
            },
        )
        organization_type_code = self.api_instance.create(
            Code,
            {
                "code": "C70793",
                "codeSystem": self._cdisc_code_system,
                "codeSystemVersion": self._cdisc_code_system_version,
                "decode": "Clinical Study Sponsor",
            },
        )
        doc_status_code = self.api_instance.create(
            Code,
            {
                "code": "C25425",
                "codeSystem": self._cdisc_code_system,
                "codeSystemVersion": self._cdisc_code_system_version,
                "decode": "Approved",
            },
        )
        protocol_code = self.api_instance.create(
            Code,
            {
                "code": "C70817",
                "codeSystem": self._cdisc_code_system,
                "codeSystemVersion": self._cdisc_code_system_version,
                "decode": "Protocol",
            },
        )
        global_code = self.api_instance.create(
            Code,
            {
                "code": "C68846",
                "codeSystem": self._cdisc_code_system,
                "codeSystemVersion": self._cdisc_code_system_version,
                "decode": "Global",
            },
        )
        global_scope = self.api_instance.create(GeographicScope, {"type": global_code})
        approval_date_code = self.api_instance.create(
            Code,
            {
                "code": "C132352",
                "codeSystem": self._cdisc_code_system,
                "codeSystemVersion": self._cdisc_code_system_version,
                "decode": "Sponsor Approval Date",
            },
        )

        # Study Title
        study_title = self.api_instance.create(
            StudyTitle, {"text": title, "type": title_type}
        )

        # Governance dates
        approval_date = self.api_instance.create(
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
        organization = self.api_instance.create(
            Organization,
            {
                "name": "Sponsor",
                "type": organization_type_code,
                "identifier": "To be provided",
                "identifierScheme": "To be provided",
                "legalAddress": None,
            },
        )
        study_identifier = self.api_instance.create(
            StudyIdentifier,
            {"text": identifier, "scopeId": organization.id},
        )

        # Documenta
        study_definition_document_version = self.api_instance.create(
            StudyDefinitionDocumentVersion,
            {
                "version": "1",
                "status": doc_status_code,
                "dateValues": [approval_date],
            },
        )
        study_definition_document = self.api_instance.create(
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

        study_version = self.api_instance.create(
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
        study = self.api_instance.create(
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

    def decode_phase(self, text) -> AliasCode:
        phase_map = [
            (
                ["0", "PRE-CLINICAL", "PRE CLINICAL"],
                {"code": "C54721", "decode": "Phase 0 Trial"},
            ),
            (["1", "I"], {"code": "C15600", "decode": "Phase I Trial"}),
            (["1-2"], {"code": "C15693", "decode": "Phase I/II Trial"}),
            (["1/2"], {"code": "C15693", "decode": "Phase I/II Trial"}),
            (["1/2/3"], {"code": "C198366", "decode": "Phase I/II/III Trial"}),
            (["1/3"], {"code": "C198367", "decode": "Phase I/III Trial"}),
            (["1A", "IA"], {"code": "C199990", "decode": "Phase Ia Trial"}),
            (["1B", "IB"], {"code": "C199989", "decode": "Phase Ib Trial"}),
            (["2", "II"], {"code": "C15601", "decode": "Phase II Trial"}),
            (["2-3", "II-III"], {"code": "C15694", "decode": "Phase II/III Trial"}),
            (["2A", "IIA"], {"code": "C49686", "decode": "Phase IIa Trial"}),
            (["2B", "IIB"], {"code": "C49688", "decode": "Phase IIb Trial"}),
            (["3", "III"], {"code": "C15602", "decode": "Phase III Trial"}),
            (["3A", "IIIA"], {"code": "C49687", "decode": "Phase IIIa Trial"}),
            (["3B", "IIIB"], {"code": "C49689", "decode": "Phase IIIb Trial"}),
            (["4", "IV"], {"code": "C15603", "decode": "Phase IV Trial"}),
            (["5", "V"], {"code": "C47865", "decode": "Phase V Trial"}),
        ]
        for tuple in phase_map:
            if text in tuple[0]:
                entry = tuple[1]
                cdisc_phase_code = self.cdisc_code(entry["code"], entry["decode"])
                return self.alias_code(cdisc_phase_code)
        cdisc_phase_code = self.cdisc_code(
            "C48660",
            "[Trial Phase] Not Applicable",
        )
        return self.alias_code(cdisc_phase_code)

    def cdisc_code(self, code: str, decode: str) -> Code:
        return self.api_instance.create(
            Code,
            {
                "code": code,
                "codeSystem": self._cdisc_code_system,
                "codeSystemVersion": self._cdisc_code_system_version,
                "decode": decode,
            },
        )

    def alias_code(self, standard_code: Code) -> AliasCode:
        return self.api_instance.create(AliasCode, {"standardCode": standard_code})

    def sponsor(self, sponsor_name: str) -> Organization:
        sponsor_code = self.cdisc_code("C70793", "Clinical Study Sponsor")
        return self.api_instance.create(
            Organization,
            {
                "name": sponsor_name,
                "label": sponsor_name,
                "type": sponsor_code,
                "identifier": "---------",
                "identifierScheme": "DUNS",
                #                "legalAddress": address,
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
