# MANUAL: do not regenerate
#
# Within each StudyAmendment, collect all DocumentContentReference
# instances (StudyAmendment.changes[].changedSections[]) grouped by
# appliesToId. For each (appliesToId, sectionNumber) the set of
# distinct sectionTitles must have size <= 1, and vice versa for
# (appliesToId, sectionTitle) → sectionNumbers. A violation in either
# direction is a failure, reported against the offending reference.
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00196(RuleTemplate):
    """
    DDF00196: There must be a one-to-one relationship between referenced section number and title within a study amendment.

    Applies to: DocumentContentReference
    Attributes: sectionNumber, sectionTitle
    """

    def __init__(self):
        super().__init__(
            "DDF00196",
            RuleTemplate.ERROR,
            "There must be a one-to-one relationship between referenced section number and title within a study amendment.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for amendment in data.instances_by_klass("StudyAmendment"):
            refs = []
            for change in amendment.get("changes") or []:
                if not isinstance(change, dict):
                    continue
                for ref in change.get("changedSections") or []:
                    if isinstance(ref, dict):
                        refs.append(ref)
            # (appliesToId, sectionNumber) → set of sectionTitles
            num_to_titles: dict = defaultdict(set)
            # (appliesToId, sectionTitle) → set of sectionNumbers
            title_to_nums: dict = defaultdict(set)
            for ref in refs:
                applies = ref.get("appliesToId")
                num = ref.get("sectionNumber")
                title = ref.get("sectionTitle")
                if num is not None:
                    num_to_titles[(applies, num)].add(title)
                if title is not None:
                    title_to_nums[(applies, title)].add(num)
            for ref in refs:
                applies = ref.get("appliesToId")
                num = ref.get("sectionNumber")
                title = ref.get("sectionTitle")
                bad_numbers = num is not None and len(num_to_titles[(applies, num)]) > 1
                bad_titles = (
                    title is not None and len(title_to_nums[(applies, title)]) > 1
                )
                if bad_numbers or bad_titles:
                    self._add_failure(
                        "DocumentContentReference has an inconsistent sectionNumber↔sectionTitle mapping within the amendment",
                        "DocumentContentReference",
                        "sectionNumber, sectionTitle",
                        data.path_by_id(ref["id"]),
                    )
        return self._result()
