from pydantic import BaseModel, ConfigDict


class StudyName(BaseModel):
    model_config = ConfigDict(strict=False)

    identifier: str = ""
    acronym: str = ""
    compound: str = ""


class SafetyEventReportingInput(BaseModel):
    """One row of the M11 9.2 reporting table (GitHub 109). ``event_type`` is
    the text: a C217287 term, or any other text, which is held as Other."""

    model_config = ConfigDict(strict=False)

    event_type: str
    other_event_type: str = ""
    situational_scope: str = ""
    reporting_period_start: str = ""
    reporting_period_end: str = ""
    reporting_timing: str = ""
    reporting_method: str = ""
    backup_reporting_method: str = ""


class StudyInput(BaseModel):
    model_config = ConfigDict(strict=False)

    name: StudyName = StudyName()
    label: str = ""
    version: str = ""
    rationale: str = ""
    sponsor_approval_date: str = ""
    confidentiality: str = ""
    original_protocol: str = ""
    safety_event_reporting: list[SafetyEventReportingInput] = []
