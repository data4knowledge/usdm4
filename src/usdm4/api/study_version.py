from datetime import date
from typing import List, Literal, Union
from typing_extensions import deprecated
from .api_base_model import ApiBaseModelWithId
from .code import Code
from .identifier import StudyIdentifier, ReferenceIdentifier
from .study_design import (
    StudyDesign,
    InterventionalStudyDesign,
    ObservationalStudyDesign,
)
from .governance_date import GovernanceDate
from .study_amendment import StudyAmendment
from .study_title import StudyTitle
from .eligibility_criterion import EligibilityCriterionItem
from .narrative_content import NarrativeContentItem
from .comment_annotation import CommentAnnotation
from .abbreviation import Abbreviation
from .study_role import StudyRole
from .organization import Organization
from .study_intervention import StudyIntervention
from .administrable_product import AdministrableProduct
from .medical_device import MedicalDevice
from .product_organization_role import ProductOrganizationRole
from .biomedical_concept import BiomedicalConcept
from .biomedical_concept_category import BiomedicalConceptCategory
from .biomedical_concept_surrogate import BiomedicalConceptSurrogate
from .syntax_template_dictionary import SyntaxTemplateDictionary
from .study_definition_document import (
    StudyDefinitionDocument,
    StudyDefinitionDocumentVersion,
)
from .condition import Condition
from .extension import ExtensionAttribute
from .extensions_d4k import (
    CS_EXT_URL,
    OV_EXT_URL,
    CC_EXT_URL,
    CN_EXT_URL,
    ME_EXT_URL,
    SS_EXT_URL,
    SAL_EXT_URL,
)


class StudyVersion(ApiBaseModelWithId):
    versionIdentifier: str
    rationale: str
    documentVersionIds: List[str] = []
    dateValues: List[GovernanceDate] = []
    amendments: List[StudyAmendment] = []
    businessTherapeuticAreas: List[Code] = []
    studyIdentifiers: List[StudyIdentifier]
    referenceIdentifiers: List[ReferenceIdentifier] = []
    studyDesigns: List[Union[InterventionalStudyDesign, ObservationalStudyDesign]] = []
    titles: List[StudyTitle]
    eligibilityCriterionItems: List[EligibilityCriterionItem] = []
    narrativeContentItems: List[NarrativeContentItem] = []
    abbreviations: List[Abbreviation] = []
    roles: List[StudyRole] = []
    organizations: List[Organization] = []
    studyInterventions: List[StudyIntervention] = []
    administrableProducts: List[AdministrableProduct] = []
    medicalDevices: List[MedicalDevice] = []
    productOrganizationRoles: List[ProductOrganizationRole] = []
    biomedicalConcepts: List[BiomedicalConcept] = []
    bcCategories: List[BiomedicalConceptCategory] = []
    bcSurrogates: List[BiomedicalConceptSurrogate] = []
    dictionaries: List[SyntaxTemplateDictionary] = []
    conditions: List[Condition] = []
    notes: List[CommentAnnotation] = []
    instanceType: Literal["StudyVersion"]

    def confidentiality_statement(self) -> str:
        ext: ExtensionAttribute = self.get_extension(CS_EXT_URL)
        return ext.valueString if ext else ""

    def original_version(self) -> bool:
        ext: ExtensionAttribute = self.get_extension(OV_EXT_URL)
        return ext.valueBoolean if ext else False

    def first_amendment(self) -> StudyAmendment | None:
        if self.amendments:
            all_items = {x.id: x for x in self.amendments}
            all_ids = list(all_items.keys())
            prev_ids = [x.previousId for x in self.amendments]
            first = list(set(all_ids) - set(prev_ids))
            if first:
                return all_items[first[0]]
        return None

    def get_title(self, title_type):
        for title in self.titles:
            if title.type.decode == title_type:
                return title
        return None

    def sponsor_organization(self) -> Organization | None:
        org = self._find_first_organization("C70793")
        if org is None:
            # Fallback, find a sponsor organization, temporary
            org = next((x for x in self.organizations if x.type.code == "C54149"), None)
        return org

    def sponsor_identifier(self) -> StudyIdentifier | None:
        org = self.sponsor_organization()
        if org:
            for identifier in self.studyIdentifiers:
                if identifier.scopeId == org.id:
                    return identifier
        return None

    @deprecated("Use sponsor_organization method")
    def sponsor(self) -> Organization:
        map = self.organization_map()
        for x in self.studyIdentifiers:
            if x.is_sponsor(map):
                return map[x.scopeId]
        return None

    def sponsor_identifier_text(self) -> StudyIdentifier:
        identifier = self.sponsor_identifier()
        return identifier.text if identifier else ""

    def sponsor_name(self) -> str:
        org: Organization = self.sponsor_organization()
        return org.name if org else ""

    def sponsor_label(self) -> str:
        org: Organization = self.sponsor_organization()
        return org.label if org else ""

    def sponsor_label_name(self) -> str:
        label = self.sponsor_label()
        return label if label else self.sponsor_name()

    def sponsor_address(self) -> str:
        org: Organization = self.sponsor_organization()
        if org:
            return org.legalAddress.text if org.legalAddress else ""
        return ""

    def co_sponsor_organization(self) -> Organization | None:
        return self._find_first_organization("C215669")

    def co_sponsor_name(self) -> str:
        org: Organization = self.co_sponsor_organization()
        return org.name if org else ""

    def co_sponsor_label(self) -> str:
        org: Organization = self.co_sponsor_organization()
        return org.label if org else ""

    def co_sponsor_label_name(self) -> str:
        label = self.co_sponsor_label()
        return label if label else self.co_sponsor_name()

    def co_sponsor_address(self) -> str:
        org: Organization = self.co_sponsor_organization()
        if org:
            return org.legalAddress.text if org.legalAddress else ""
        return ""

    def local_sponsor_organization(self) -> Organization | None:
        return self._find_first_organization("C215670")

    def local_sponsor_name(self) -> str:
        org: Organization = self.local_sponsor_organization()
        return org.name if org else ""

    def local_sponsor_label(self) -> str:
        org: Organization = self.local_sponsor_organization()
        return org.label if org else ""

    def local_sponsor_label_name(self) -> str:
        label = self.local_sponsor_label()
        return label if label else self.local_sponsor_name()

    def local_sponsor_address(self) -> str:
        org: Organization = self.local_sponsor_organization()
        if org:
            return org.legalAddress.text if org.legalAddress else ""
        return ""

    def manufacturer_organization(self) -> Organization | None:
        return self._find_first_organization("C25392")

    def device_manufacturer_organization(self) -> Organization | None:
        manufacturers: list[Organization] = self._find_organizations("C25392")
        return next((x for x in manufacturers if x.type.code == "C215661"), None)

    def device_manufacturer_name(self) -> str:
        org: Organization = self.device_manufacturer_organization()
        return org.name if org else ""

    def device_manufacturer_label(self) -> str:
        org: Organization = self.device_manufacturer_organization()
        return org.label if org else ""

    def device_manufacturer_label_name(self) -> str:
        label = self.device_manufacturer_label()
        return label if label else self.device_manufacturer_name()

    def device_manufacturer_address(self) -> str:
        org: Organization = self.device_manufacturer_organization()
        if org:
            return org.legalAddress.text if org.legalAddress else ""
        return ""

    def nct_identifier(self) -> StudyIdentifier:
        return self._identifier_of_type("C172240")

    def nmpa_identifier(self) -> StudyIdentifier:
        return self._identifier_of_type("C218688")
    
    def who_identifier(self) -> StudyIdentifier:
        return self._identifier_of_type("C218689")
    
    def ema_identifier(self) -> StudyIdentifier:
        return self._identifier_of_type("C218684")
    
    def fda_ind_identifier(self) -> StudyIdentifier:
        return self._identifier_of_type("C218685")
    
    def fda_ide_identifier(self) -> StudyIdentifier:
        return self._identifier_of_type("C218686")

    def jrct_identifier(self) -> StudyIdentifier:
        return self._identifier_of_type("C218687")
    
    def other_identifiers(self) -> list[StudyIdentifier]:
        result = []
        si = self.sponsor_identifier()
        for identifier in self.studyIdentifiers:
            if identifier is si:
                continue
            if identifier.of_type().code == "C218690":
                result.append(identifier)
        return result
    
    def _identifier_of_type(self, code: str) -> StudyIdentifier:
        return next((x for x in self.studyIdentifiers if x.of_type().code == code), None)

    def _find_first_organization(self, role_code: str) -> Organization | None:
        orgs = self._find_organizations(role_code)
        return orgs[0] if len(orgs) > 0 else None

    def _find_organizations(self, role_code: str) -> list[Organization]:
        role = next((x for x in self.roles if x.code.code == role_code), None)
        return [self.organization(x) for x in role.organizationIds] if role else []

    def regulatory_identifiers(self) -> list[StudyIdentifier]:
        results = []
        for identifier in self.studyIdentifiers:
            org = self.organization(identifier.scopeId)
            if org and org.type.code == "C188863":
                results.append(identifier)
        return results

    def registry_identifiers(self) -> list[StudyIdentifier]:
        results = []
        for identifier in self.studyIdentifiers:
            org = self.organization(identifier.scopeId)
            if org and org.type.code == "C93453":
                results.append(identifier)
        return results

    def organization(self, id: str) -> Organization:
        return next((x for x in self.organizations if x.id == id), None)

    def criterion_item(self, id: str) -> EligibilityCriterionItem:
        return next((x for x in self.eligibilityCriterionItems if x.id == id), None)

    def intervention(self, id: str) -> StudyIntervention:
        return next((x for x in self.studyInterventions if x.id == id), None)

    def condition(self, id: str) -> Condition:
        return next((x for x in self.conditions if x.id == id), None)

    def phases(self) -> str:
        return ", ".join([sd.phase_as_text() for sd in self.studyDesigns])

    def official_title_text(self) -> str:
        for x in self.titles:
            if x.is_official():
                return x.text
        return ""

    def short_title_text(self) -> str:
        for x in self.titles:
            if x.is_short():
                return x.text
        return ""

    def acronym_text(self) -> str:
        for x in self.titles:
            if x.is_acronym():
                return x.text
        return ""

    def official_title(self) -> StudyIdentifier:
        for x in self.titles:
            if x.is_official():
                return x
        return None

    def short_title(self) -> StudyIdentifier:
        for x in self.titles:
            if x.is_short():
                return x
        return None

    def acronym(self) -> StudyIdentifier:
        for x in self.titles:
            if x.is_acronym():
                return x
        return None

    @deprecated("Use the method relating to the document")
    def protocol_date(self) -> GovernanceDate:
        for x in self.dateValues:
            if x.type.code == "C71476":
                return x
        return ""

    def approval_date(self) -> GovernanceDate | None:
        for x in self.dateValues:
            if x.type.code == "C71476":
                return x
        return None

    @deprecated("Use the method relating to the document")
    def protocol_date_value(self) -> date:
        for x in self.dateValues:
            if x.type.code == "C71476":
                return x.dateValue
        return ""

    def approval_date_value(self) -> date | None:
        for x in self.dateValues:
            if x.type.code == "C71476":
                return x.dateValue
        return None

    def approval_date_text(self) -> str | None:
        for x in self.dateValues:
            if x.type.code == "C71476":
                return x.dateValue.strftime("%Y-%m-%d")
        return None

    def sponsor_approval_location(self) -> str:
        ext: ExtensionAttribute = self.get_extension(SAL_EXT_URL)
        return ext.valueString if ext else ""

    def find_study_design(self, id: str) -> StudyDesign:
        return next((x for x in self.studyDesigns if x.id == id), None)

    def documents(
        self,
        document_map: dict[
            str, dict[StudyDefinitionDocument, StudyDefinitionDocumentVersion]
        ],
    ) -> list[dict[StudyDefinitionDocument, StudyDefinitionDocumentVersion]]:
        return [document_map[x] for x in self.documentVersionIds]

    def to_html(
        self,
        template: str,
        document_map: dict[
            str, dict[StudyDefinitionDocument, StudyDefinitionDocumentVersion]
        ],
    ) -> str | None:
        sddv: StudyDefinitionDocumentVersion
        if sddv := self.study_document_version(template, document_map):
            return sddv.to_html(self.narrative_content_item_map())
        return None

    def study_document_version(
        self,
        template: str,
        document_map: dict[
            str, dict[StudyDefinitionDocument, StudyDefinitionDocumentVersion]
        ],
    ) -> StudyDefinitionDocumentVersion | None:
        docs_info = self.documents(document_map)
        for doc_info in docs_info:
            study_document: StudyDefinitionDocument = doc_info["document"]
            if study_document.templateName.upper() == template.upper():
                return doc_info["version"]
        return None

    def compound_codes(self) -> str:
        ext: ExtensionAttribute = self.get_extension(CC_EXT_URL)
        return ext.valueString if ext else ""

    def compound_names(self) -> str:
        ext: ExtensionAttribute = self.get_extension(CN_EXT_URL)
        return ext.valueString if ext else ""

    def medical_expert(self) -> str:
        ext: ExtensionAttribute = self.get_extension(ME_EXT_URL)
        return ext.valueString if ext else ""

    def sponsor_signatory(self) -> str:
        ext: ExtensionAttribute = self.get_extension(SS_EXT_URL)
        return ext.valueString if ext else ""

    def role_map(self) -> dict[str, StudyRole]:
        return {x.id: x for x in self.roles}

    def organization_map(self) -> dict[str, Organization]:
        return {x.id: x for x in self.organizations}

    def eligibility_critieria_item_map(self) -> dict[str, EligibilityCriterionItem]:
        return {x.id: x for x in self.eligibilityCriterionItems}

    def narrative_content_item_map(self) -> dict[str, NarrativeContentItem]:
        return {x.id: x for x in self.narrativeContentItems}
