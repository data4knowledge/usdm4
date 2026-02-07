from typing import List, Literal
from datetime import date
from .api_base_model import ApiBaseModelWithId
from .code import Code
from .governance_date import GovernanceDate
from .narrative_content import NarrativeContent, NarrativeContentItem
from .comment_annotation import CommentAnnotation


class StudyDefinitionDocumentVersion(ApiBaseModelWithId):
    version: str
    status: Code
    dateValues: List[GovernanceDate] = []
    contents: List[NarrativeContent] = []
    notes: List[CommentAnnotation] = []
    instanceType: Literal["StudyDefinitionDocumentVersion"]

    def approval_date(self) -> GovernanceDate | None:
        for x in self.dateValues:
            if x.type.code == "C71476":
                return x
        return None

    def approval_date_value(self) -> date | None:
        for x in self.dateValues:
            if x.type.code == "C71476":
                return x.dateValue
        return None

    def approval_date_text(self) -> str | None:
        for x in self.dateValues:
            if x.type.code == "C71476":
                return x.dateValue.strftime("%Y-%m-%d")
        return None

    def narrative_content_in_order(self):
        sections = []
        narrative_content = self._first_narrative_content()
        while narrative_content:
            sections.append(narrative_content)
            narrative_content = next(
                (x for x in self.contents if x.id == narrative_content.nextId), None
            )
        return sections

    def find_narrative_content(self, id: str) -> NarrativeContent | None:
        map = self.narrative_content_map()
        return map[id] if id in map else None

    def find_narrative_content_by_number(
        self, section_number: str
    ) -> NarrativeContent | None:
        return next(
            (x for x in self.contents if x.sectionNumber == section_number), None
        )

    def find_narrative_content_by_title(
        self, section_title: str
    ) -> NarrativeContent | None:
        return next(
            (
                x
                for x in self.contents
                if x.sectionTitle.upper() == section_title.upper()
            ),
            None,
        )

    def to_html(
        self, narrative_content_item_map: dict[str, NarrativeContentItem]
    ) -> str:
        result = ""
        narrative_contents = self.narrative_content_in_order()
        narrative_content: NarrativeContent
        for narrative_content in narrative_contents:
            result += narrative_content.format_heading()
            content: NarrativeContentItem = narrative_content.content_item(
                narrative_content_item_map
            )
            if content:
                result += content.text
        return result

    def narrative_content_map(self) -> dict[NarrativeContent]:
        return {x.id: x for x in self.contents}

    def _first_narrative_content(self) -> NarrativeContent:
        return next((x for x in self.contents if not x.previousId and x.nextId), None)
