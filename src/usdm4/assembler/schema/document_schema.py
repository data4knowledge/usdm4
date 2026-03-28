from pydantic import BaseModel, ConfigDict


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(strict=False)

    label: str = ""
    version: str = ""
    status: str = "Draft"
    template: str = ""
    version_date: str = ""


class Section(BaseModel):
    model_config = ConfigDict(strict=False)

    section_number: str
    section_title: str = ""
    text: str = ""


class DocumentInput(BaseModel):
    model_config = ConfigDict(strict=False)

    document: DocumentMetadata = DocumentMetadata()
    sections: list[Section] = []
