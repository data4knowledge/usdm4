from typing import List, Literal, Union
from pydantic import Field
from .api_base_model import ApiBaseModel
from .study_definition_document import (
    StudyDefinitionDocument,
    StudyDefinitionDocumentVersion,
)
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

    def document_by_template_name(self, name: str) -> StudyDefinitionDocument | None:
        return next(
            (x for x in self.documentedBy if x.templateName.upper() == name.upper()),
            None,
        )

    def document_templates(self) -> list[str]:
        return [x.templateName for x in self.documentedBy]

    def document_map(
        self,
    ) -> dict[str, dict[StudyDefinitionDocument, StudyDefinitionDocumentVersion]]:
        result = {}
        for doc in self.documentedBy:
            for version in doc.versions:
                result[version.id] = {"document": doc, "version": version}
        return result

    def first_version(self) -> StudyVersion | None:
        return self.versions[0] if len(self.versions) > 0 else None
