from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00171(RuleTemplate):
    """
    DDF00171: The expanded text for all abbreviations defined for a study version are expected to be unique.

    Applies to: Abbreviation
    Attributes: expandedText
    """

    def __init__(self):
        super().__init__(
            "DDF00171",
            RuleTemplate.WARNING,
            "The expanded text for all abbreviations defined for a study version are expected to be unique.",
        )

    # TODO: implement. MED_TEXT: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions@$sv.
    #       (
    #         $filter($sv.abbreviations,function($v,$i,$a)
    #           {$count($a[$lowercase($.expandedText)=$lowercase($v.expandedText)])>1}
    #         )
    #         ~> $sort(function($l,$r){$lowercase($l.expandedText)>$lowercase($r.expandedText)})
    #       ).
    #       {
    #         "instanceType": instanceType,
    #         "id": id,
    #         "path": _path,
    #         "StudyVersion.id": $sv.id,
    #         "StudyVersion.versionIdentifier": $sv.versionIdentifier,
    #         "abbreviatedText": abbreviatedText,
    #         "expandedText": expandedText
    #       }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00171: not yet implemented")
