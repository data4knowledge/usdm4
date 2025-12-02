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
