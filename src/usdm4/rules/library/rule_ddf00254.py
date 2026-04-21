from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00254(RuleTemplate):
    """
    DDF00254: An activity must only reference child activities that are specified within the same study design.

    Applies to: Activity
    Attributes: children
    """

    def __init__(self):
        super().__init__(
            "DDF00254",
            RuleTemplate.ERROR,
            "An activity must only reference child activities that are specified within the same study design.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Activity"):
            scope = data.parent_by_klass(item["id"], ['InterventionalStudyDesign', 'ObservationalStudyDesign'])
            if scope is None:
                continue
            # Collect ids of same-class siblings within this scope
            sibling_ids = {
                sib["id"]
                for sib in data.instances_by_klass("Activity")
                if (sp := data.parent_by_klass(sib["id"], ['InterventionalStudyDesign', 'ObservationalStudyDesign'])) is not None
                and sp["id"] == scope["id"]
            }
            for ref_id in item.get("childIds") or []:
                if ref_id not in sibling_ids:
                    self._add_failure(
                        f"childIds references {ref_id!r} outside the same scope",
                        "Activity",
                        "childIds",
                        data.path_by_id(item["id"]),
                    )
        return self._result()
