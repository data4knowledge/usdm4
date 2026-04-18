from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00246(RuleTemplate):
    """
    DDF00246: Any parameter name referenced in a tag in the text should be specified in the data dictionary parameter maps.

    Applies to: EligibilityCriterionItem, Characteristic, Condition, Objective, Endpoint, IntercurrentEvent
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00246",
            RuleTemplate.ERROR,
            "Any parameter name referenced in a tag in the text should be specified in the data dictionary parameter maps.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     **.study.versions@$sv.
    #       ($sv.**[$type(text)="string" and $contains(text,/usdm:tag/)])@$st.
    #         (
    #           $dict := $sv.dictionaries[id=$st.dictionaryId];
    #           $valid_tags := $dict.parameterMaps.tag;
    #           $match ($st.text,
    #                       /<usdm:tag((?=[^>]* name=\"(\w+)\")[^>]*)(\/>|><\/usdm:tag>)/
    #           ) [
    #               $not(
    #                 $st.dictionaryId and
    #                 $dict and
    #                 groups[1] in $valid_tags
    #               )
    #             ].
    #             {
    #               "instanceType": $st.instanceType,
    #               "id": $st.id,
    #               "path": $st._path,
    #               "name": $st.name,
    #               "Parameter reference": match,
    #               "Parameter name": groups[1],
    #               "dictionaryId": $st.dictionaryId,
    #               "SyntaxTemplateDictionary.name": $dict.name,
    #               "Issue": $st.dictionaryId 
    #                         ? $dict
    #                             ? "Parameter not in dictionary"
    #                             : "dictionaryId is invalid"
    #                         : "dictionaryId is missing"
    #             }
    #         )

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00246: not yet implemented")
