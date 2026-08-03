from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00069(RuleTemplate):
    """
    DDF00069: Each combination of arm and epoch must occur no more than once within a study design.

    Applies to: StudyCell
    Attributes: arm, epoch
    """

    def __init__(self):
        super().__init__(
            "DDF00069",
            RuleTemplate.ERROR,
            "Each combination of arm and epoch must occur no more than once within a study design.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        seen: dict = {}
        for item in data.instances_by_klass("StudyCell"):
            scope = data.parent_by_klass(
                item["id"], ["InterventionalStudyDesign", "ObservationalStudyDesign"]
            )
            if scope is None:
                continue
            key = (scope["id"], (item.get("armId"), item.get("epochId")))
            if key in seen:
                self._add_failure(
                    f"Duplicate ({item.get('armId')!r}, {item.get('epochId')!r}) within scope",
                    "StudyCell",
                    "armId, epochId",
                    data.path_by_id(item["id"]),
                )
            else:
                seen[key] = item["id"]
        return self._result()
