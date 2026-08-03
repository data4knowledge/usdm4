# MANUAL: do not regenerate
#
# NarrativeContent must have at least one of `childIds` (non-empty list)
# or `contentItemId` (non-empty string). Both absent = failure.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00163(RuleTemplate):
    """
    DDF00163: Narrative content is expected to point to a child and/or to a content item text.

    Applies to: NarrativeContent
    Attributes: childIds, contentItemId
    """

    def __init__(self):
        super().__init__(
            "DDF00163",
            RuleTemplate.WARNING,
            "Narrative content is expected to point to a child and/or to a content item text.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for nc in data.instances_by_klass("NarrativeContent"):
            has_child = bool(nc.get("childIds"))
            has_content_item = bool(nc.get("contentItemId"))
            if not (has_child or has_content_item):
                self._add_failure(
                    "NarrativeContent has neither childIds nor contentItemId",
                    "NarrativeContent",
                    "childIds, contentItemId",
                    data.path_by_id(nc["id"]),
                )
        return self._result()
