from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00198(RuleTemplate):
    """
    DDF00198: Each study definition document version is expected to be referenced by either a study version or a study design.

    Applies to: StudyVersion, ObservationalStudyDesign, InterventionalStudyDesign
    Attributes: documentVersions
    """

    def __init__(self):
        super().__init__(
            "DDF00198",
            RuleTemplate.WARNING,
            "Each study definition document version is expected to be referenced by either a study version or a study design.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study@$s.
    #       $s.documentedBy@$sdd.
    #         $sdd.versions[$not(id in $append($s.versions.documentVersionIds,$s.versions.studyDesigns.documentVersionIds))].
    #         {
    #           "instanceType": instanceType,
    #           "id": id,
    #           "path": _path,
    #           "StudyDefinitionDocument.id": $sdd.id,
    #           "StudyDefinitionDocument.name": $sdd.name,
    #           "version": version
    #         }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00198: not yet implemented")
