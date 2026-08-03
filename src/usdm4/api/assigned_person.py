from typing import Union, Literal
from .api_base_model import ApiBaseModelWithIdNameLabelAndDesc
from .person_name import PersonName
from .extension import ExtensionAttribute
from .extensions_d4k import APCD_EXT_URL


class AssignedPerson(ApiBaseModelWithIdNameLabelAndDesc):
    personName: PersonName
    jobTitle: str
    organizationId: Union[str, None] = None
    instanceType: Literal["AssignedPerson"]

    def contact_details(self) -> str | None:
        ext: ExtensionAttribute = self.get_extension(APCD_EXT_URL)
        return ext.valueString if ext else None
