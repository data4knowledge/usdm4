from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00010(RuleTemplate):
    """
    DDF00010: The names of all child instances of the same parent class must be unique.

    Applies to: All
    Attributes: name
    """

    def __init__(self):
        super().__init__(
            "DDF00010",
            RuleTemplate.ERROR,
            "The names of all child instances of the same parent class must be unique.",
        )

    # TODO: implement. HIGH_UNIQUE_WITHIN_SCOPE without scope info — ambiguous (global vs per-parent vs intra-attribute). Review rule text.
    # Reference — CORE JSONata condition (semantics, not executed):
    #     **.*[id and instanceType and name].$
    #         {
    #             instanceType: {
    #                 name: [$.{"id": id, "path": _path, "name": name}]
    #             } ~> $sift(function($v,$k){$count($v)>1})
    #         }
    #         ~> $each(function($v,$k){
    #             $v.*.{
    #                 "instanceType":$k,
    #                 "id": id,
    #                 "path": path,
    #                 "name": name
    #             }})
    #         ~> $reduce($append)

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00010: not yet implemented")
