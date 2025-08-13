import uuid4
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.assembler.identification_assembler import IdentificationAssembler
from usdm4.assembler.study_design_assembler import StudyDesignAssembler
from usdm4.assembler.document_assembler import DocumentAssembler
from usdm4.builder.builder import Builder
from usdm4.api.study import Study
from usdm4.api.study_version import StudyVersion
from usdm4.api.geographic_scope import GeographicScope
from usdm4.api.governance_date import GovernanceDate


class StudyAssembler(BaseAssembler):
    MODULE = "usdm4.assembler.study_assembler.StudyAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        """
        Initialize the StudyAssembler.

        Args:
            builder (Builder): The builder instance for creating USDM objects
            errors (Errors): Error handling instance for logging issues
        """
        super().__init__(builder, errors)
        self._study = None
        self._dates = []

    def execute(
        self,
        data: dict,
        identification_assembler: IdentificationAssembler,
        study_design_assembler: StudyDesignAssembler,
        document_assembler: DocumentAssembler,
    ) -> None:
        try:
            params = {
                "versionIdentifier": data["version"],
                "rationale": data["rationale"],
                "titles": identification_assembler.titles,
                "dateValues": self._dates + document_assembler.dates,
                "studyDesigns": [study_design_assembler.study_design],
                "documentVersionIds": [document_assembler.document_version.id],
                "studyIdentifiers": identification_assembler.identifiers,
                "organizations": identification_assembler.organizations,
                "amendments": [],
                "eligibilityCriterionItems": [],
            }
            study_version = self._builder.create(StudyVersion, params)
            self._study = self._builder.create(
                Study,
                {
                    "id": uuid4(),
                    "name": data["name"],
                    "label": data["label"],
                    "description": "The top-level study container",
                    "versions": [study_version],
                    "documentedBy": [document_assembler.document],
                },
            )
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception(f"Failed during creation of study", e, location)

    @property
    def study(self) -> Study:
        return self._study

    def _create_dates(self, data: dict) -> None:
        try:
            sponsor_approval_date_code = self._builder.cdisc_code(
                "C132352", "Protocol Approval by Sponsor Date"
            )
            global_code = self._builder.cdisc_code("C68846", "Global")
            global_scope = self._builder.create(GeographicScope, {"type": global_code})
            approval_date = self._builder.create(
                GovernanceDate,
                {
                    "name": "Approval Date",
                    "type": sponsor_approval_date_code,
                    "dateValue": data["sponsor_approval_date"],
                    "geographicScopes": [global_scope],
                },
            )
            if approval_date:
                self._dates.append(approval_date)
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "_create_dates")
            self._errors.exception(
                f"Failed during creation of governace date", e, location
            )
