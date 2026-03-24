from pydantic import BaseModel, ConfigDict


class EpochItem(BaseModel):
    model_config = ConfigDict(strict=False)

    text: str = ""


class VisitItem(BaseModel):
    model_config = ConfigDict(strict=False)

    text: str = ""
    references: list[str] = []


class TimepointItem(BaseModel):
    model_config = ConfigDict(strict=False, extra="allow")

    text: str = ""
    value: int | float | str = 0
    unit: str = "day"
    index: int | str = 0


class WindowItem(BaseModel):
    model_config = ConfigDict(strict=False)

    before: int = 0
    after: int = 0
    unit: str = "day"


class ActivityVisit(BaseModel):
    model_config = ConfigDict(strict=False)

    index: int
    references: list[str] = []


class ActivityActions(BaseModel):
    model_config = ConfigDict(strict=False)

    bcs: list[str] = []


class ActivityItem(BaseModel):
    model_config = ConfigDict(strict=False, extra="allow")

    name: str = ""
    visits: list[ActivityVisit] = []
    children: list["ActivityItem"] = []
    actions: ActivityActions = ActivityActions()


class ConditionItem(BaseModel):
    model_config = ConfigDict(strict=False)

    reference: str = ""
    text: str = ""


class EpochsBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[EpochItem] = []


class VisitsBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[VisitItem] = []


class TimepointsBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[TimepointItem] = []


class WindowsBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[WindowItem] = []


class ActivitiesBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[ActivityItem] = []


class ConditionsBlock(BaseModel):
    model_config = ConfigDict(strict=False)

    found: bool = False
    items: list[ConditionItem] = []


class TimelineInput(BaseModel):
    model_config = ConfigDict(strict=False)

    epochs: EpochsBlock = EpochsBlock()
    visits: VisitsBlock = VisitsBlock()
    timepoints: TimepointsBlock = TimepointsBlock()
    windows: WindowsBlock = WindowsBlock()
    activities: ActivitiesBlock = ActivitiesBlock()
    conditions: ConditionsBlock = ConditionsBlock()
