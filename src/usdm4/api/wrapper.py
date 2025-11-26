from typing import Union
from .api_base_model import ApiBaseModel
from .study import Study
from .study_version import StudyVersion


class Wrapper(ApiBaseModel):
    study: Study
    usdmVersion: str
    systemName: Union[str, None] = None
    systemVersion: Union[str, None] = None

    def first_version(self) -> StudyVersion | None:
        return self.study.first_version() if self.study else None
