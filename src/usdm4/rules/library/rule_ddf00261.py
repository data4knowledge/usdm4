from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00261(RuleTemplate):
    """
    DDF00261: If a geographic scope type is global then no code is expected to specify the specific area within scope while if it is not global then a code is expected to specify the specific area within scope.

    Applies to: GeographicScope
    Attributes: code
    """

    def __init__(self):
        super().__init__(
            "DDF00261",
            RuleTemplate.WARNING,
            "If a geographic scope type is global then no code is expected to specify the specific area within scope while if it is not global then a code is expected to specify the specific area within scope.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     **[instanceType="GeographicScope" and (type.code="C68846")=($exists(code) and code)].
    #       {
    #         "instanceType": instanceType,
    #         "id": id,
    #         "path": _path,
    #         "type.code": type.code,
    #         "type.decode": type.decode,
    #         "code.standardCode.code": code.standardCode.code,
    #         "code.standardCode.decode": code.standardCode.decode
    #       }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00261: not yet implemented")
