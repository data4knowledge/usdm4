import json
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.builder.builder import Builder
from usdm4.assembler.identification_assembler import IdentificationAssembler
from usdm4.assembler.population_assembler import PopulationAssembler
from usdm4.assembler.document_assembler import DocumentAssembler
from usdm4.assembler.study_design_assembler import StudyDesignAssembler
from usdm4.assembler.study_assembler import StudyAssembler
from usdm4.api.study import Study


class Assembler:
    MODULE = "usdm4.assembler.assembler.Assembler"

    def __init__(self, root_path: str, errors: Errors):
        self._errors = errors
        self._builder = Builder(root_path, self._errors)
        self._identification_assembler = IdentificationAssembler(
            self._builder, self._errors
        )
        self._population_assembler = PopulationAssembler(self._builder, self._errors)
        self._document_assembler = DocumentAssembler(self._builder, self._errors)
        self._study_design_assembler = StudyDesignAssembler(self._builder, self._errors)
        self._study_assembler = StudyAssembler(self._builder, self._errors)

    def execute(self, data: dict) -> Study | None:
        try:
            self._identification_assembler.execute(data["identification"])
            self._document_assembler.execute(data["document"])
            self._population_assembler.execute(data["population"])
            self._study_design_assembler.execute(
                data["study_design"], self._population_assembler
            )
            self._study_assembler.execute(
                data["study"],
                self._identification_assembler,
                self._study_design_assembler,
                self._document_assembler,
            )
            return self._study_assembler.study
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception(f"Failed during assembler", e, location)