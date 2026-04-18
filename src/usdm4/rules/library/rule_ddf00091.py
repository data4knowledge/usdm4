from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00091(RuleTemplate):
    """
    DDF00091: When a condition applies to a procedure, activity, biomedical concept, biomedical concept category, or biomedical concept surrogate then an instance must be available in the corresponding class with the specified id.

    Applies to: Condition
    Attributes: appliesTo
    """

    def __init__(self):
        super().__init__(
            "DDF00091",
            RuleTemplate.ERROR,
            "When a condition applies to a procedure, activity, biomedical concept, biomedical concept category, or biomedical concept surrogate then an instance must be available in the corresponding class with the specified id.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     (
    #       $idityp:=$.study.versions.**[id]{id:instanceType};
    #       $.study.versions.**.conditions.appliesToIds.
    #         {
    #           "instanceType": %.instanceType,
    #           "id": %.id,
    #           "path": %._path,
    #           "name": %.name,
    #           "appliesTo id": $,
    #           "appliesTo instanceType": $ in $keys($idityp) ? $lookup($idityp,$) : "[Invalid id]"
    #         }
    #         [
    #           $not(`appliesTo instanceType` in
    #             [
    #               'Procedure',
    #               'Activity',
    #               'BiomedicalConcept',
    #               'BiomedicalConceptCategory',
    #               'BiomedicalConceptSurrogate'
    #             ]
    #           )
    #         ]
    #     )

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00091: not yet implemented")
