from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.builder.builder import Builder
from usdm4.api.code import Code
from usdm4.api.address import Address
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

    TITLE_TYPES = [
        "brief",
        "official",
        "public",
        "scientific",
        "acronym",
    ]

    TITLE_CODES = {
        "brief": {"code": "C207615", "decode": "Brief Study Title"},
        "official": {"code": "C207616", "decode": "Official Study Title"},
        "public": {"code": "C207617", "decode": "Public Study Title"},
        "scientific": {"code": "C207618", "decode": "Scientific Study Title"},
        "acronym": {"code": "C207646", "decode": "Study Acronym"},
    }

    ORG_CODES = {
        "registry": {"code": "C93453", "decode": "Clinical Study Registry"},
        "regulator": {"code": "C188863", "decode": "Regulatory Agency"},
        "healthcare": {"code": "C21541", "decode": "Healthcare Facility"},
        "pharma": {"code": "C54149", "decode": "Pharmaceutical Company"},
        "lab": {"code": "C37984", "decode": "Laboratory"},
        "cro": {"code": "C54148", "decode": "Contract Research Organization"},
        "gov": {"code": "C199144", "decode": "Government Institute"},
        "academic": {"code": "C18240", "decode": "Academic Institution"},
        "medical_device": {"code": "C215661", "decode": "Medical Device Company"},
    }
    STANDARD_ORGS = {
        "ct.gov": {
            "type": "registry",
            "name": "CT.GOV",
            "label": "ClinicalTrials.gov",
            "description": "The US clinical trials registry",
            "identifier": "ClinicalTrials.gov",
            "identifierScheme": "National Institute of Health, US Government",
            "legalAddress": {
                "lines": ["National Library of Medicine", "8600 Rockville Pike"],
                "city": "Bethesda",
                "district": "",
                "state": "MD",
                "postalCode": "20894",
                "country": "USA",
            },
        },
        "ema": {
            "type": "regulator",
            "name": "EMA",
            "label": "European Medicines Agency",
            "description": "The European medicines regulator",
            "identifier": "EMA",
            "identifierScheme": "European Union",
            "legalAddress": {
                "lines": ["Domenico Scarlattilaan 6"],
                "city": "Amsterdam",
                "district": "",
                "state": "",
                "postalCode": "1083 HS",
                "country": "NL",
            },
        },
        "fda": {
            "type": "regulator",
            "name": "FDA",
            "label": "Food and Drug Admionistration",
            "identifier": "FDA",
            "description": "The US medicines regulator",
            "identifierScheme": "Health and Human Services, US Government",
            "legalAddress": {
                "lines": ["10903 New Hampshire Ave"],
                "city": "Silver Spring",
                "district": "",
                "state": "MD",
                "postalCode": "20903",
                "country": "USA",
            },
        },
    }

    def __init__(self, builder: Builder, errors: Errors):
        super().__init__(builder, errors)
        self._titles = []
        self._organizations = []
        self._identifiers = []

    def execute(self, data: dict) -> None:


# data spec
      {
         "titles": {
            "brief": <string>,
            "official": <string>,
            "public": <string>,
            "scientific": <string>,
            "acronym": <string>,
         },
         "identifiers": {


#     "identifier": : <string>,
#     "scope": {
#         "non_standard": {
#             "type": <string>,
#             "name": <string>,
#             "description": "",
#             "label": "",
#             "identifier": "",
#             "identifierScheme": "",
#             "legalAddress": {
#                 "lines": [],
#                 "city": "",
#                 "district": "",
#                 "state": "",
#                 "postalCode": "",
#                 "country": ""
#             }
#         },
#         "standard": ""
#     }
# }
         }

        
        # Titles
        for type, text in data["titles"].items():
            if type in self.TITLE_TYPES:
                title_type = self._builder.cdisc_code(
                    self.TITLE_CODES[type]["code"], self.TITLE_CODES[type]["decode"]
                )
                self._titles.append(
                    self._builder.create(StudyTitle, {"text": text, "type": title_type})
                )

        # Identifiers
        id_details: dict
        for id_details in data["identifiers"]:
            organization: dict = (
                self.STANDARD_ORGS[id_details["standard"]]
                if "standard" in id_details
                else id_details["non_standard"]
            )

            # Address
            organization["address"]["country"] = self._builder.iso3166_code(
                organization["address"]["country"]
            )
            organization["legalAddress"] = self._builder.create(
                Address, organization["legalAddress"]
            )

            # Organization
            org_type = organization["type"]
            organization["type"] = self._builder.cdisc_code(
                self.ORG_CODES[org_type]["code"], self.ORG_CODES[org_type]["decode"]
            )
            org: Organization = self._builder.create(Organization, organization)
            self._organizations.append(org)

            # Identifier
            identifier = self.create(
                StudyIdentifier, {"text": identifier["identifier"], "scopeId": org.id}
            )
            self._identifiers.append(identifier)


