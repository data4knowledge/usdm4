from typing import List, Literal
from .api_base_model import ApiBaseModelWithId
from .code import Code
from .governance_date import GovernanceDate
from .narrative_content import NarrativeContent
from .comment_annotation import CommentAnnotation


class StudyDefinitionDocumentVersion(ApiBaseModelWithId):
    version: str
    status: Code
    dateValues: List[GovernanceDate] = []
    contents: List[NarrativeContent] = []
    childIds: List[str] = []
    notes: List[CommentAnnotation] = []
    instanceType: Literal["StudyDefinitionDocumentVersion"]

    DELIMITER = "."

    def narrative_content_in_order(self):
        sections = []
        narrative_content = self._first_narrative_content()
        while narrative_content:
            sections.append(narrative_content)
            narrative_content = next(
                (x for x in self.contents if x.id == narrative_content.nextId), None
            )
        return sections

    def can_add_sibling_section(self, content: NarrativeContent):
        potential_section_key = self._increment_section_number(content)
        return self._section_is_permitted(potential_section_key)

    def can_add_child_section(self, content: NarrativeContent):
        potential_section_key = self._child_section_number(content)
        return self._section_is_permitted(potential_section_key)

    def add_sibling_section(self, content: NarrativeContent):
        new_section_key = self._increment_section_number (content)
        if self._section_is_permitted(new_section_key):
            self._data[new_section_key] = {
                "sectionNumber": new_section_key.replace("-", "."),
                "sectionTitle": "To Be Provided",
                "name": "",
                "text": "",
            }
            self._write()
            result = new_section_key
        else:
            result = None

    def add_child_section(self, content: NarrativeContent):
        new_section_key = self._child_section_number (content)
        if self._section_is_permitted(new_section_key):
            self._data[new_section_key] = {
                "sectionNumber": new_section_key.replace("-", "."),
                "sectionTitle": "To Be Provided",
                "name": "",
                "text": "",
            }
            self._write()
            result = new_section_key
        else:
            result = None

    def _first_narrative_content(self) -> NarrativeContent:
        return next((x for x in self.contents if not x.previousId and x.nextId), None)

    def _section_is_permitted(self, content: NarrativeContent):
        result = True if content: NarrativeContent not in self._data.keys() else False
        return result
    
    def _increment_section_number(self, content: NarrativeContent):
        parts = content: NarrativeContent.split(self.DELIMITER)
        parts[-1] = str(int(parts[-1]) + 1)
        return self.DELIMITER.join(parts)

    def _child_section_number(self, content: NarrativeContent):
        parts = content: NarrativeContent.split(self.DELIMITER)
        parts.append('1')
        return self.DELIMITER.join(parts)
