from typing import Literal
from typing_extensions import deprecated
from .api_base_model import ApiBaseModelWithId
from .organization import Organization
from .code import Code
from .extensions_d4k import SIT_EXT_URL
from .extension import ExtensionAttribute


class Identifier(ApiBaseModelWithId):
    text: str
    scopeId: str
    instanceType: Literal["Identifier"]


class ReferenceIdentifier(Identifier):
    type: Code
    instanceType: Literal["ReferenceIdentifier"]


class StudyIdentifier(Identifier):
    instanceType: Literal["StudyIdentifier"]

    @deprecated("Use roles not identifiers to find a sponsor organization")
    def is_sponsor(self, organization_map: dict) -> bool:
        org = organization_map[self.scopeId]
        return True if org.type.code == "C54149" else False

    def scoped_by(self, organization_map: dict) -> Organization:
        return organization_map[self.scopeId]

    def of_type(self) -> Code | None:
        ext: ExtensionAttribute = self.get_extension(SIT_EXT_URL)
        return ext.valueCode if ext else None


class AdministrableProductIdentifier(Identifier):
    instanceType: Literal["AdministrableProductIdentifier"]


class MedicalDeviceIdentifier(Identifier):
    type: Code
    instanceType: Literal["MedicalDeviceIdentifier"]
