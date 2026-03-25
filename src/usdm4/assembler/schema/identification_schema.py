from pydantic import BaseModel, ConfigDict


class Titles(BaseModel):
    model_config = ConfigDict(strict=False)

    brief: str = ""
    official: str = ""
    public: str = ""
    scientific: str = ""
    acronym: str = ""


class Address(BaseModel):
    model_config = ConfigDict(strict=False)

    lines: list[str] = []
    city: str = ""
    district: str = ""
    state: str = ""
    postalCode: str = ""
    country: str = ""


class NonStandardOrganization(BaseModel):
    model_config = ConfigDict(strict=False)

    type: str
    role: str | None = None
    name: str = ""
    description: str = ""
    label: str = ""
    identifier: str = ""
    identifierScheme: str = ""
    legalAddress: Address | None = None


class IdentifierScope(BaseModel):
    model_config = ConfigDict(strict=False)

    standard: str | None = None
    non_standard: NonStandardOrganization | None = None


class StudyIdentifier(BaseModel):
    model_config = ConfigDict(strict=False)

    identifier: str
    scope: IdentifierScope


class RoleOrganization(BaseModel):
    model_config = ConfigDict(strict=False)

    name: str = ""
    address: Address | None = None


class MedicalExpert(BaseModel):
    model_config = ConfigDict(strict=False)

    name: str | None = None
    reference: list[str] | None = None


class OtherIdentification(BaseModel):
    model_config = ConfigDict(strict=False)

    medical_expert: MedicalExpert | None = None
    sponsor_signatory: str | None = None
    compound_names: str | None = None
    compound_codes: str | None = None


class IdentificationInput(BaseModel):
    model_config = ConfigDict(strict=False)

    titles: Titles = Titles()
    identifiers: list[StudyIdentifier] = []
    roles: dict[str, RoleOrganization | None] = {}
    other: OtherIdentification = OtherIdentification()
