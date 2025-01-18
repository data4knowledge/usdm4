from typing import Union
from usdm.api.api_base_model import ApiBaseModel
from usdm.api.study import Study
from usdm.api.study_title import StudyTitle
from usdm.api.code import Code
from usdm.api.study_definition_document_version import StudyDefinitionDocumentVersion
from usdm.api.study_definition_document import StudyDefinitionDocument
from usdm.api.study_version import StudyVersion
from usdm.api.identifier import StudyIdentifier
from usdm.api.organization import Organization
from usdm.api.governance_date import GovernanceDate
from usdm.api.geographic_scope import GeographicScope
from usdm.base.globals import Globals
from usdm.base.api_instance import APIInstance
from usdm import __model_version__, __package_name__, __package_version__
from uuid import uuid4


class Wrapper(ApiBaseModel):
    study: Study
    usdmVersion: str
    systemName: Union[str, None] = None
    systemVersion: Union[str, None] = None

    @classmethod
    def minimum(cls, title: str, identifier: str, version: str) -> "Wrapper":
        """
        Create a minimum study with the given title, identifier, and version.
        """
        globals = Globals()
        globals.clear()
        api_instance = APIInstance(globals)
        cdisc_code_system = "cdisc.org"
        cdisc_code_system_version = "2023-12-15"

        # Define the codes to be used in the study
        english_code = api_instance.create(
            Code,
            {
                "code": "en",
                "codeSystem": "ISO 639-1",
                "codeSystemVersion": "2007",
                "decode": "English",
            },
        )
        study_type_code = api_instance.create(
            Code,
            {
                "code": "C98388",
                "codeSystem": cdisc_code_system,
                "codeSystemVersion": cdisc_code_system_version,
                "decode": "Interventional Study",
            },
        )
        organization_type_code = api_instance.create(
            Code,
            {
                "code": "C70793",
                "codeSystem": cdisc_code_system,
                "codeSystemVersion": cdisc_code_system_version,
                "decode": "Clinical Study Sponsor",
            },
        )
        doc_status_code = api_instance.create(
            Code,
            {
                "code": "C25425",
                "codeSystem": cdisc_code_system,
                "codeSystemVersion": cdisc_code_system_version,
                "decode": "Approved",
            },
        )
        protocol_code = api_instance.create(
            Code,
            {
                "code": "C70817",
                "codeSystem": cdisc_code_system,
                "codeSystemVersion": cdisc_code_system_version,
                "decode": "Protocol",
            },
        )
        global_code = api_instance.create(
            Code,
            {
                "code": "C68846",
                "codeSystem": cdisc_code_system,
                "codeSystemVersion": cdisc_code_system_version,
                "decode": "Global",
            },
        )
        global_scope = api_instance.create(GeographicScope, {"type": global_code})
        approval_date_code = api_instance.create(
            Code,
            {
                "code": "C132352",
                "codeSystem": cdisc_code_system,
                "codeSystemVersion": cdisc_code_system_version,
                "decode": "Sponsor Approval Date",
            },
        )

        # Study Title
        study_title = api_instance.create(
            StudyTitle, {"text": title, "type": study_type_code}
        )

        # Governance dates
        approval_date = api_instance.create(
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
        organization = api_instance.create(
            Organization,
            {
                "name": "Sponsor",
                "type": organization_type_code,
                "identifier": "To be provided",
                "identifierScheme": "To be provided",
                "legalAddress": None,
            },
        )
        study_identifier = api_instance.create(
            StudyIdentifier,
            {"text": identifier, "scopeId": organization.id},
        )

        # Documenta
        study_definition_document_version = api_instance.create(
            StudyDefinitionDocumentVersion,
            {
                "version": "1",
                "status": doc_status_code,
                "dateValues": [approval_date],
            },
        )
        study_definition_document = api_instance.create(
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

        study_version = api_instance.create(
            StudyVersion,
            {
                "versionIdentifier": "1",
                "rationale": "To be provided",
                "titles": [study_title],
                "studyDesigns": [],
                "documentVersionId": study_definition_document_version.id,
                "studyIdentifiers": [study_identifier],
                "studyPhase": None,
                "dateValues": [approval_date],
                "amendments": [],
                "organizations": [organization],
            },
        )
        study = api_instance.create(
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
        result = api_instance.create(
            Wrapper,
            {
                "study": study,
                "usdmVersion": __model_version__,
                "systemName": f"Python {__package_name__} Package",
                "systemVersion": __package_version__,
            },
        )

        print(f"Errors: {globals.errors.errors.dump(0)}")
        return result
