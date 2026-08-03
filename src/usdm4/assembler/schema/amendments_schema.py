from pydantic import BaseModel, ConfigDict, Field


class AmendmentReasons(BaseModel):
    model_config = ConfigDict(strict=False)

    primary: str = ""
    secondary: str = ""


class SubstantialChange(BaseModel):
    model_config = ConfigDict(strict=False)

    substantial: bool = False
    reason: str = ""


class SafetyAndRights(BaseModel):
    model_config = ConfigDict(strict=False)

    safety: SubstantialChange = SubstantialChange()
    rights: SubstantialChange = SubstantialChange()


class ReliabilityAndRobustness(BaseModel):
    model_config = ConfigDict(strict=False)

    reliability: SubstantialChange = SubstantialChange()
    robustness: SubstantialChange = SubstantialChange()


class AmendmentImpact(BaseModel):
    model_config = ConfigDict(strict=False)

    safety_and_rights: SafetyAndRights = SafetyAndRights()
    reliability_and_robustness: ReliabilityAndRobustness = ReliabilityAndRobustness()


class AmendmentEnrollment(BaseModel):
    model_config = ConfigDict(strict=False)

    value: int | str = ""
    unit: str = ""


class AmendmentScope(BaseModel):
    model_config = ConfigDict(
        strict=False,
        populate_by_name=True,
    )

    global_: bool = Field(False, alias="global")
    unknown: list[str] = []
    countries: list[str] = []
    regions: list[str] = []
    sites: list[str] = []


class AmendmentChange(BaseModel):
    model_config = ConfigDict(strict=False)

    section: str = ""
    description: str = ""
    rationale: str = ""


class AmendmentsInput(BaseModel):
    model_config = ConfigDict(strict=False)

    identifier: str = ""
    summary: str = ""
    reasons: AmendmentReasons = AmendmentReasons()
    impact: AmendmentImpact = AmendmentImpact()
    enrollment: AmendmentEnrollment | None = None
    scope: AmendmentScope | None = None
    changes: list[AmendmentChange] = []
