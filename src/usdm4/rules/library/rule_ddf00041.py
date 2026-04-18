from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00041(RuleTemplate):
    """
    DDF00041: Within a study design, there must be at least one endpoint with level primary.

    Applies to: Endpoint
    Attributes: level
    """

    def __init__(self):
        super().__init__(
            "DDF00041",
            RuleTemplate.ERROR,
            "Within a study design, there must be at least one endpoint with level primary.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     $.study.versions.studyDesigns.
    #       {
    #           "instanceType": instanceType,
    #           "id": id,
    #           "path": _path,
    #           "name": name,
    #           "# Primary endpoints": $count(objectives.endpoints[level.code="C94496"])
    #       }[`# Primary endpoints` = 0][]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00041: not yet implemented")
