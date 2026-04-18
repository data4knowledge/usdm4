# MANUAL: do not regenerate
#
# Reverse of DDF00080: every defined StudyEpoch must be reachable from
# at least one SAI's epochId. Flag epochs with no referring SAI.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00099(RuleTemplate):
    """
    DDF00099: All epochs are expected to be referred to from a scheduled Activity Instance.

    Applies to: StudyEpoch (referenced from ScheduledActivityInstance)
    Attributes: epochId
    """

    def __init__(self):
        super().__init__(
            "DDF00099",
            RuleTemplate.WARNING,
            "All epochs are expected to be referred to from a scheduled Activity Instance.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        referenced_epoch_ids = {
            sai.get("epochId")
            for sai in data.instances_by_klass("ScheduledActivityInstance")
            if sai.get("epochId")
        }
        for epoch in data.instances_by_klass("StudyEpoch"):
            if epoch.get("id") not in referenced_epoch_ids:
                self._add_failure(
                    "StudyEpoch is not referenced from any ScheduledActivityInstance",
                    "StudyEpoch",
                    "epochId",
                    data.path_by_id(epoch["id"]),
                )
        return self._result()
