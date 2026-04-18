from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00189(RuleTemplate):
    """
    DDF00189: Every study role must apply to either a study version or at least one study design, but not both.

    Applies to: StudyRole
    Attributes: appliesTo
    """

    def __init__(self):
        super().__init__(
            "DDF00189",
            RuleTemplate.ERROR,
            "Every study role must apply to either a study version or at least one study design, but not both.",
        )

    # TODO: implement. mutual-exclusion with class='StudyRole' attrs=['appliesTo'] — needs at least 2 attrs.
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions@$sv.
    #       ($sv.roles
    #         [
    #           $not(
    #               appliesToIds and
    #                 (
    #                     ($count(appliesToIds)=1 and appliesToIds[0]=$sv.id) or
    #                     $count(appliesToIds)=$count(appliesToIds[$ in $sv.studyDesigns.id])
    #                 )
    #           )
    #         ]
    #       )@$r.
    #         {
    #           "instanceType": $r.instanceType,
    #           "id": $r.id,
    #           "path": $r._path,
    #           "name": $r.name,
    #           "code": $r.code.decode,
    #           "appliesToIds": $r.appliesToIds[],
    #           "StudyVersion.id": $sv.id,
    #           "StudyVersion.studyDesigns.id": $sv.studyDesigns.id
    #         }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00189: not yet implemented")
