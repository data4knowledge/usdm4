from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00236(RuleTemplate):
    """
    DDF00236: If a synonym is specified then it is not expected to be equal to the label of the biomedical concept (case insensitive).

    Applies to: BiomedicalConcept
    Attributes: synonyms
    """

    def __init__(self):
        super().__init__(
            "DDF00236",
            RuleTemplate.WARNING,
            "If a synonym is specified then it is not expected to be equal to the label of the biomedical concept (case insensitive).",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions.biomedicalConcepts)@$bc.
    #       $bc.
    #           [(  {
    #                   "instanceType": instanceType,
    #                   "id": id,
    #                   "path": _path,
    #                   "name": name,
    #                   "label/synonym": label,
    #                   "synonyms": "["&$join(synonyms,", ")&"]",
    #                   "check":  $exists($filter(synonyms,function($v){($lowercase($v) =$lowercase(label))}) )
    #               }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00236: not yet implemented")
