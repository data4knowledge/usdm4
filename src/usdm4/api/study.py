from typing import List, Literal, Union
from pydantic import Field
from .api_base_model import ApiBaseModel
from .study_definition_document import StudyDefinitionDocument
from .study_version import StudyVersion
from uuid import UUID


class Study(ApiBaseModel):
    id: Union[UUID, None] = None
    name: str = Field(min_length=1)
    description: Union[str, None] = None
    label: Union[str, None] = None
    versions: List[StudyVersion] = []
    documentedBy: List[StudyDefinitionDocument] = []
    instanceType: Literal["Study"]

    def document_by_template_name(self, name: str) -> StudyDefinitionDocument:
        return next(
            (x for x in self.documentedBy if x.templateName.upper() == name.upper()),
            None,
        )

    def document_templates(self):
        return [x.templateName for x in self.documentedBy]

    def first_version(self) -> StudyVersion:
        try:
            return self.versions[0]
        except Exception:
            return None
        
    def summary(self) -> dict:
        study_version = self.first_version()
        return {
            "acronym": study_version.acronym_text(),
            "full_title": study_version.official_title_text(),
            "sponsor_protocol_identifier": study_version.sponsor_identifier_text(),
            "version_number": study_version.versionIdentifier,
            "version_date": study_version.protocol_date_value(),
            "trial_phase": ", ".join([x.studyPhase.standardCode.decode for x in study_version.studyDesigns]),
            "short_title": study_version.short_title_text(),
            "sponsor_name": study_version.sponsor_name(),
            "sponsor_address": study_version.sponsor_address(),
            "sponsor_approval_date": study_version.approval_date_value(),
        }