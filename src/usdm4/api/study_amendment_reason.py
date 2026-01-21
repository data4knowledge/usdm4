from typing import Literal, Union
from .api_base_model import ApiBaseModelWithId
from .code import Code


class StudyAmendmentReason(ApiBaseModelWithId):
    code: Code
    otherReason: Union[str, None] = None
    instanceType: Literal["StudyAmendmentReason"]

    def reason_as_text(self) -> str:
        return self.code.decode

    def other_reason_as_text(self) -> str:
        return self.otherReason if self.otherReason else ""
