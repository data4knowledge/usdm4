from pydantic import BaseModel, ConfigDict


class InclusionExclusion(BaseModel):
    model_config = ConfigDict(strict=False)

    inclusion: list[str] = []
    exclusion: list[str] = []


class PopulationInput(BaseModel):
    model_config = ConfigDict(strict=False)

    label: str = ""
    inclusion_exclusion: InclusionExclusion = InclusionExclusion()
