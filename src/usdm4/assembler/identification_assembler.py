from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.builder.builder import Builder
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
from usdm4.api.biomedical_concept import BiomedicalConcept


from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation

class IdentificationAssembler(BaseAssembler):
    MODULE = "usdm4.assembler.base_assembler.BaseAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        super().__init__(builder, errors)
        self._titles = []
        self._organizations = []
        self._identifiers = []

    def execute(self, data: dict) -> None:
        
        title_type = self._builder.cdisc_code("C207616", "Official Study Title")
        organization_type_code = self._builder.cdisc_code("C70793", "Clinical Study Sponsor")
        
        # Titles
        self._titles.append(self._builder.create(StudyTitle, {"text": data['titles']['official'], "type": title_type}))

        # Organizations
        sponsor: Organization = self.create(
            Organization,
            {
                "name": "Sponsor",
                "type": organization_type_code,
                "identifier": "To be provided",
                "identifierScheme": "To be provided",
                "legalAddress": None,
            },
        )
        self._organizations.append(sponsor)

        # Identifiers
        identifier = self.create(
            StudyIdentifier,
            {"text": data['identifiers']['sponsor'], "scopeId": sponsor.id}
        )
        self._identifiers.append(identifier)
