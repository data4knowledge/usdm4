import json
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.assembler.base_assembler import BaseAssembler
from usdm4.builder.builder import Builder
from usdm4.api.narrative_content import NarrativeContent, NarrativeContentItem
from usdm4.api.study_definition_document import StudyDefinitionDocument
from usdm4.api.study_definition_document_version import StudyDefinitionDocumentVersion
from usdm4.api.geographic_scope import GeographicScope
from usdm4.api.governance_date import GovernanceDate


class DocumentAssembler(BaseAssembler):
    MODULE = "usdm4.assembler.document_assembler.DocumentAssembler"
    DIV_OPEN_NS = '<div xmlns="http://www.w3.org/1999/xhtml">'
    DIV_CLOSE = "</div>"

    def __init__(self, builder: Builder, errors: Errors):
        """
        Initialize the DocumentAssembler.

        Args:
            builder (Builder): The builder instance for creating USDM objects
            errors (Errors): Error handling instance for logging issues
        """
        super().__init__(builder, errors)
        self._document: StudyDefinitionDocument = None
        self._document_version: StudyDefinitionDocumentVersion = None
        self._contents = []
        self._dates = []

    def execute(self, data: dict) -> None:
        try:
            document: dict = data["document"]
            sections: list[dict] = data["sections"]
            self._create_date(document)
            self._document_version = self._builder.create(
                StudyDefinitionDocumentVersion,
                {
                    "version": document["version"],
                    "status": document["status"],
                },
            )
            language = self._builder.iso639_code("en")
            doc_type = self._builder.cdisc_code("C70817", "Protocol")
            self._document = self._builder.create(
                StudyDefinitionDocument,
                {
                    "name": self._label_to_name(document["label"]),
                    "label": document["label"],
                    "description": "Protocol Document",
                    "language": language,
                    "type": doc_type,
                    "templateName": document["template"],
                    "versions": [self._document_version],
                },
            )
            _ = self._section_to_narrative(None, sections, 0, 1)
            self._builder.double_link(
                self._document_version.contents, "previousId", "nextId"
            )
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "execute")
            self._errors.exception(f"Failed during creation of population", e, location)

    @property
    def document(self) -> StudyDefinitionDocument:
        return self._document

    @property
    def document_version(self) -> StudyDefinitionDocumentVersion:
        return self._document_version

    @property
    def dates(self) -> list[GovernanceDate]:
        return self._dates

    def _section_to_narrative(
        self, parent: NarrativeContent, sections: list[dict], index: int, level: int
    ) -> int:
        process = True
        previous = None
        local_index = index
        location = KlassMethodLocation(self.MODULE, "_section_to_narrative")
        while process:
            section = sections[local_index]
            section_level = self._section_level(section)
            if section_level == level:
                sn = section["section_number"] if section["section_number"] else ""
                dsn = True if sn else False
                st = section["section_title"] if section["section_title"] else ""
                dst = True if st else False
                nc_text = f"{self.DIV_OPEN_NS}{section['text']}{self.DIV_CLOSE}"
                nci = self._builder.create(
                    NarrativeContentItem,
                    {"name": f"NCI-{sn}", "text": nc_text},
                )
                nc = self._builder.create(
                    NarrativeContent,
                    {
                        "name": f"NC-{sn}",
                        "sectionNumber": sn,
                        "displaySectionNumber": dsn,
                        "sectionTitle": st,
                        "displaySectionTitle": dst,
                        "contentItemId": nci.id,
                        "childIds": [],
                        "previousId": None,
                        "nextId": None,
                    },
                )
                self._document_version.contents.append(nc)
                self._contents.append(nci)
                if parent:
                    parent.childIds.append(nc.id)
                previous = nc
                local_index += 1
            elif section_level > level:
                if previous:
                    local_index = self._section_to_narrative(
                        previous, sections, local_index, level + 1
                    )
                else:
                    self._errors.error(
                        "No previous section set while processing sections", location
                    )
                    local_index += 1
            elif section_level < level:
                return local_index
            if local_index >= len(sections):
                process = False
        return local_index

    def _section_level(self, section: dict) -> int:
        section_number: str = section["section_number"]
        text = section_number[:-1] if section_number.endswith(".") else section_number
        return len(text.split("."))

    def _create_date(self, data: dict) -> None:
        try:
            protocol_date_code = self._builder.cdisc_code(
                "C207598",
                "Protocol Effective Date",
            )
            global_code = self._builder.cdisc_code("C68846", "Global")
            global_scope = self._builder.create(GeographicScope, {"type": global_code})
            protocol_date = self._builder.create(
                GovernanceDate,
                {
                    "name": "PROTOCOL-DATE",
                    "type": protocol_date_code,
                    "dateValue": data["version_date"],
                    "geographicScopes": [global_scope],
                },
            )
            if protocol_date:
                self._dates.append(protocol_date)
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "_data")
            self._errors.exception(
                f"Failed during creation of governance date", e, location
            )
