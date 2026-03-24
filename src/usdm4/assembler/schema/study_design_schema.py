from pydantic import BaseModel, ConfigDict


class StudyDesignInput(BaseModel):
    model_config = ConfigDict(strict=False)

    label: str = ""
    rationale: str = ""
    trial_phase: str = ""
