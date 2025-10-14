import json
from typing import Union, List
from pydantic import BaseModel, Field
from .extension import ExtensionAttribute
from .serialize import serialize_as_json


class ApiBaseModel(BaseModel):
    def __init__(self, *args, **kwargs):
        kwargs["instanceType"] = self.__class__.__name__
        super().__init__(*args, **kwargs)

    def to_json(self):
        return json.dumps(self, default=serialize_as_json)


class ApiBaseModelWithIdOnly(ApiBaseModel):
    id: str = Field(min_length=1)

    def label_name(self) -> str:
        return ""


class ApiBaseModelWithId(ApiBaseModelWithIdOnly):
    extensionAttributes: List[ExtensionAttribute] = []

    def get_extension(self, url: str) -> ExtensionAttribute:
        return next(
            (x for x in self.extensionAttributes if x.url.upper() == url.upper()), None
        )


class ApiBaseModelWithIdAndDesc(ApiBaseModelWithId):
    description: Union[str, None] = None


class ApiBaseModelWithIdAndName(ApiBaseModelWithId):
    name: str = Field(min_length=1)

    def label_name(self) -> str:
        return self.name


class ApiBaseModelWithIdNameAndLabel(ApiBaseModelWithIdAndName):
    label: Union[str, None] = None

    def label_name(self) -> str:
        return self.label if self.label else self.name


class ApiBaseModelWithIdNameLabelAndDesc(ApiBaseModelWithIdNameAndLabel):
    description: Union[str, None] = None


class ApiBaseModelWithIdNameAndDesc(ApiBaseModelWithIdAndName):
    description: Union[str, None] = None
