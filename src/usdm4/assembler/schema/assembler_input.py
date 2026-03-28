from pydantic import BaseModel, ConfigDict

from usdm4.assembler.schema.identification_schema import IdentificationInput
from usdm4.assembler.schema.document_schema import DocumentInput
from usdm4.assembler.schema.population_schema import PopulationInput
from usdm4.assembler.schema.amendments_schema import AmendmentsInput
from usdm4.assembler.schema.study_design_schema import StudyDesignInput
from usdm4.assembler.schema.study_schema import StudyInput
from usdm4.assembler.schema.timeline_schema import TimelineInput


class AssemblerInput(BaseModel):
    model_config = ConfigDict(strict=False, extra="ignore")

    identification: IdentificationInput
    document: DocumentInput
    population: PopulationInput
    study_design: StudyDesignInput
    study: StudyInput
    amendments: AmendmentsInput = AmendmentsInput()
    soa: TimelineInput | None = None

    @classmethod
    def validate_strict(cls, data: dict) -> tuple["AssemblerInput", list[str]]:
        """Validate with warnings for empty required fields."""
        instance = cls.model_validate(data)
        warnings = []
        if not instance.identification.titles.official:
            warnings.append("identification.titles.official is empty")
        if not instance.document.document.version:
            warnings.append("document.document.version is empty")
        if not instance.study.version:
            warnings.append("study.version is empty")
        return instance, warnings
