from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00161(RuleTemplate):
    """
    DDF00161: The ordering of activities (using the previous and next attributes) must include the parents (e.g. activities referring to children) preceding their children.

    Applies to: Activity
    Attributes: previous, next
    """

    def __init__(self):
        super().__init__(
            "DDF00161",
            RuleTemplate.ERROR,
            "The ordering of activities (using the previous and next attributes) must include the parents (e.g. activities referring to children) preceding their children.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions.studyDesigns@$sd.
    #         $sd.activities@$a.
    #           (
    #             $pacts := $utils.parse_refs("childIds","children",$sd.activities);
    #             {
    #               "instanceType": $a.instanceType,
    #               "id": $a.id,
    #               "path": $a._path,
    #               "StudyDesign.id": $sd.id,
    #               "StudyDesign.name": $sd.name,
    #               "name": $a.name,
    #               "previousId": $a.previousId,
    #               "Previous Activity's childIds": $sd.activities[id=$a.previousId].childIds[],
    #               "nextId": $a.nextId,
    #               "childIds": $a.childIds[],
    #               "Parent Activity's id": $pacts[$a.id in children.id].id,
    #               "Parent Activity's other descendants' ids": $pacts[$a.id in children.id].children[id!=$a.id].[id,**.children.id].*,
    #               "Issue(s)": [
    #                             (
    #                               $a.childIds and
    #                               $not($a.nextId in $a.childIds)
    #                             )
    #                             ? "The activity has children but its nextId does not match any of its childIds.",
    #                             (
    #                               $pacts[$a.id in children.id] and
    #                               $not($a.previousId in $pacts[$a.id in children.id].[id,children[id!=$a.id].id,children[id!=$a.id].**.children.id])
    #                             )
    #                             ? "The activity is a child but its previousId does not match the id of either its Parent Activity or any of the Parent Activity's other descendants.",
    #                             (
    #                               $sd.activities[id=$a.previousId].childIds and
    #                               $not($a.id in $sd.activities[id=$a.previousId].childIds)
    #                             )
    #                             ? "The activity's id does not match any of the childIds of the Previous Activity."
    #                           ]
    #             }
    #           )[`Issue(s)`]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00161: not yet implemented")
