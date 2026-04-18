from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00231(RuleTemplate):
    """
    DDF00231: If a biospecimen retention indicates that a type of biospecimen is retained, then there must be an indication of whether the type of biospecimen includes DNA.

    Applies to: BiospecimenRetention
    Attributes: includesDNA
    """

    def __init__(self):
        super().__init__(
            "DDF00231",
            RuleTemplate.ERROR,
            "If a biospecimen retention indicates that a type of biospecimen is retained, then there must be an indication of whether the type of biospecimen includes DNA.",
        )

    # TODO: implement. MED_TEXT predicate='conditional': no template — typically a rule-specific conditional. Hand-author using the JSONata reference below.
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (study.versions)@$sv.
    #       $sv.studyDesigns@$sd.
    #       $sd.biospecimenRetentions.    [({
    #                       "instanceType": instanceType,
    #                       "id": id,
    #                       "path": _path,
    #                       "StudyDesign.id": $sd.id,
    #                       "StudyDesign.name": $sd.name,
    #                       "name": name,
    #                       "isRetained": isRetained,
    #                       "check": isRetained=true and $not(includesDNA in [true,false])
    #                   }
    #           )][check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00231: not yet implemented")
