# MANUAL: do not regenerate
#
# Each StudyDefinitionDocumentVersion has a `contents` list of
# NarrativeContent. Within that list, non-empty sectionNumber values
# must be unique. Duplicates fail, reported against each offender.
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00245(RuleTemplate):
    """
    DDF00245: Within a document version, the specified section numbers for narrative content must be unique.

    Applies to: NarrativeContent (within each StudyDefinitionDocumentVersion)
    Attributes: sectionNumber
    """

    def __init__(self):
        super().__init__(
            "DDF00245",
            RuleTemplate.ERROR,
            "Within a document version, the specified section numbers for narrative content must be unique.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sddv in data.instances_by_klass("StudyDefinitionDocumentVersion"):
            groups: dict = defaultdict(list)
            for nc in sddv.get("contents") or []:
                if not isinstance(nc, dict):
                    continue
                number = nc.get("sectionNumber")
                if number is None or number == "":
                    continue
                groups[number].append(nc)
            for number, entries in groups.items():
                if len(entries) <= 1:
                    continue
                for nc in entries:
                    self._add_failure(
                        f"NarrativeContent.sectionNumber {number!r} is not unique within the document version ({len(entries)} occurrences)",
                        "NarrativeContent",
                        "sectionNumber",
                        data.path_by_id(nc["id"]),
                    )
        return self._result()
