from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00188(RuleTemplate):
    """
    DDF00188: A planned sex must ether include a single entry of male or female or both female and male as entries.

    Applies to: StudyDesignPopulation, StudyCohort
    Attributes: plannedSex
    """

    def __init__(self):
        super().__init__(
            "DDF00188",
            RuleTemplate.ERROR,
            "A planned sex must ether include a single entry of male or female or both female and male as entries.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     ($.**[plannedSex])@$p.
    #       $p.[{
    #               "instanceType": instanceType,
    #               "id": id,
    #               "path": _path,
    #               "name": name,
    #               "plannedSex":"["&$join(plannedSex.(id & ": " & decode & " (" & code & ")"),"; ")&"]",
    #               "check": ($count(plannedSex.id) != $count($distinct(plannedSex.code))) or false in $map(plannedSex.code,function($v){$v in ["C16576","C20197"]})        
    #               }][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00188: not yet implemented")
