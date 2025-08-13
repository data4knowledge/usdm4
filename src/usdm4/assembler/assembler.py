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
    """
    Main assembler class responsible for orchestrating the assembly of a complete Study object
    from structured input data.
    
    The Assembler coordinates multiple specialized assemblers to process different domains
    of study data in the correct sequence, ensuring proper cross-references and dependencies
    are maintained throughout the assembly process.
    
    The assembly process follows a specific order to handle data dependencies:
    1. Identification (study IDs and versions)
    2. Documents (protocols and amendments) 
    3. Populations (subject populations and analysis sets)
    4. Study Design (arms, epochs, activities, timelines)
    5. Study (core study information and final assembly)
    """
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
        """
        Executes the assembly process to build a complete Study object from structured data.
        
        Args:
            data (dict): A dictionary containing all the structured data needed to assemble a study.
                        The data parameter must have the following top-level structure:
                        
                        {
                            "identification": dict,    # Study identification data (IDs, versions, etc.)
                            "document": dict,          # Document-related data (protocols, amendments, etc.)
                            "population": dict,        # Population definitions and analysis populations
                            "study_design": dict,      # Study design elements (arms, epochs, activities, etc.)
                            "study": dict             # Core study information (title, objectives, etc.)
                        }
                        
                        Each top-level key corresponds to a specific domain of study data:
                        
                        - "identification": Contains study identifiers, version information, and 
                          regulatory identifiers needed to uniquely identify the study
                          
                        - "document": Contains study definition documents, protocol versions,
                          amendments, and other document-related metadata
                          
                        - "population": Contains population definitions, analysis populations,
                          eligibility criteria, and subject enrollment information
                          
                        - "study_design": Contains the structural elements of the study design
                          including study arms, epochs, elements, activities, encounters,
                          procedures, and timeline information
                          
                        - "study": Contains the core study metadata including titles, objectives,
                          indications, interventions, and high-level study characteristics
                        
        Returns:
            Study | None: A fully assembled Study object if successful, None if assembly fails
            
        Note:
            The assembly process is sequential and interdependent:
            1. Identification data is processed first to establish study identity
            2. Document data is processed to set up protocol and amendment structure
            3. Population data is processed to define subject populations
            4. Study design data is processed (requires population data for references)
            5. Study data is processed last (requires all other components for assembly)
        """
        try:
            # Process identification data - establishes study identity and versioning
            self._identification_assembler.execute(data["identification"])
            
            # Process document data - sets up protocol documents and amendments
            self._document_assembler.execute(data["document"])
            
            # Process population data - defines subject populations and analysis sets
            self._population_assembler.execute(data["population"])
            
            # Process study design data - requires population assembler for cross-references
            self._study_design_assembler.execute(
                data["study_design"], self._population_assembler
            )
            
            # Process core study data - requires all other assemblers for final assembly
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
