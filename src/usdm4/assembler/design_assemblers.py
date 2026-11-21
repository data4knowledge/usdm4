from dataclasses import dataclass

from simple_error_log.errors import Errors

from usdm4.assembler.objectives_assembler import ObjectivesAssembler
from usdm4.assembler.population_assembler import PopulationAssembler
from usdm4.assembler.study_design_assembler import StudyDesignAssembler
from usdm4.assembler.timeline_assembler import TimelineAssembler
from usdm4.builder.builder import Builder


@dataclass
class DesignAssemblers:
    """The assemblers that build one study design (GitHub 108): its
    population, its timelines, the design itself and its objectives.

    A study with one design has one set, the ``Assembler``'s own. A study
    with several has one set per design; ``StudyAssembler`` gathers what
    each built onto the StudyVersion.
    """

    population: PopulationAssembler
    timeline: TimelineAssembler
    study_design: StudyDesignAssembler
    objectives: ObjectivesAssembler

    @classmethod
    def create(cls, builder: Builder, errors: Errors) -> "DesignAssemblers":
        return cls(
            PopulationAssembler(builder, errors),
            TimelineAssembler(builder, errors),
            StudyDesignAssembler(builder, errors),
            ObjectivesAssembler(builder, errors),
        )
