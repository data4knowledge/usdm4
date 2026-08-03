from pydantic import BaseModel, ConfigDict


class StudyName(BaseModel):
    model_config = ConfigDict(strict=False)

    identifier: str = ""
    acronym: str = ""
    compound: str = ""


class StudyInput(BaseModel):
    model_config = ConfigDict(strict=False)

    name: StudyName = StudyName()
    label: str = ""
    version: str = ""
    rationale: str = ""
    sponsor_approval_date: str = ""
    confidentiality: str = ""
    original_protocol: str = ""
