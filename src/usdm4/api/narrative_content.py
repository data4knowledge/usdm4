from typing import List, Literal, Union
from .api_base_model import ApiBaseModelWithIdAndName


class NarrativeContentItem(ApiBaseModelWithIdAndName):
    text: str
    instanceType: Literal["NarrativeContentItem"]


class NarrativeContent(ApiBaseModelWithIdAndName):
    sectionNumber: Union[str, None] = None
    sectionTitle: Union[str, None] = None
    displaySectionNumber: bool
    displaySectionTitle: bool
    childIds: List[str] = []
    previousId: Union[str, None] = None
    nextId: Union[str, None] = None
    contentItemId: Union[str, None] = None
    instanceType: Literal["NarrativeContent"]

    def content_item(
        self, narrative_content_item_map: dict
    ) -> NarrativeContentItem | None:
        return (
            narrative_content_item_map[self.contentItemId]
            if self.contentItemId in narrative_content_item_map
            else None
        )

    def level(self) -> int:
        if self.sectionNumber is None:
            result = 1
        elif self.sectionNumber.lower().startswith("appendix"):
            result = 1
        else:
            text = (
                self.sectionNumber[:-1]
                if self.sectionNumber.endswith(".")
                else self.sectionNumber
            )
            result = len(text.split("."))
        return result

    def format_heading(self) -> str:
        level = self.level()
        number = self.sectionNumber
        title = self.sectionTitle
        if number and number == "0":
            return ""
        elif number and title:
            return f"<h{level}>{number} {title}</h{level}>"
        elif number:
            return f"<h{level}>{number}</h{level}>"
        elif title:
            return f"<h{level}>{title}</h{level}>"
        else:
            return ""
