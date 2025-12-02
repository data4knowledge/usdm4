from typing import Union
from .api_base_model import ApiBaseModel
from .study import Study
from .study_version import StudyVersion
from .study_design import StudyDesign
from .study_definition_document_version import StudyDefinitionDocumentVersion


class Wrapper(ApiBaseModel):
    study: Study
    usdmVersion: str
    systemName: Union[str, None] = None
    systemVersion: Union[str, None] = None

    def first_version(self) -> StudyVersion | None:
        return self.study.first_version() if self.study else None

    def version_and_study(
        self, id: str
    ) -> tuple[StudyVersion | None, StudyDesign | None]:
        study: Study = self.study
        if study:
            version: StudyVersion = study.first_version()
            if version:
                return version, version.find_study_design(id)
        return None, None
