from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00195(RuleTemplate):
    """
    DDF00195: Each study enrollment must apply to either a geographic scope, a study site, or a study cohort.

    Applies to: SubjectEnrollment
    Attributes: forStudyCohort, forStudySite, forGeographicScope
    """

    def __init__(self):
        super().__init__(
            "DDF00195",
            RuleTemplate.ERROR,
            "Each study enrollment must apply to either a geographic scope, a study site, or a study cohort.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions@$sv.
    #       $sv.amendments@$a.
    #         $a.enrollments.
    #         (
    #           $gs:=$exists(forGeographicScope) and forGeographicScope;
    #           $ss:=$exists(forStudySiteId) and forStudySiteId;
    #           $sc:=$exists(forStudyCohortId) and forStudyCohortId;
    #           {
    #             "instanceType": instanceType,
    #             "id": id,
    #             "path": _path,
    #             "StudyAmendment.id": $a.id,
    #             "StudyAmendment.name": $a.name,
    #             "name": name,
    #             "forGeographicScope": 
    #               forGeographicScope
    #               ? forGeographicScope.(id&": "&type.decode),
    #             "forStudySiteId": 
    #               forStudySiteId
    #               ? (
    #                   $sid:=forStudySiteId;
    #                   $sid&": "&
    #                     (
    #                       $sid in $sv.organizations.managedSites.id
    #                       ? $sv.organizations.managedSites[id=$sid].name
    #                       : "Invalid forStudySiteId"
    #                     )
    #                 ),
    #             "forStudyCohortId":
    #               forStudyCohortId
    #               ? (
    #                   $cid:=forStudyCohortId;
    #                   $cid&": "&
    #                     (
    #                       $cid in $sv.**.cohorts.id
    #                       ? $sv.**.cohorts[id=$cid].name
    #                       : "Invalid forStudyCohortId"
    #                     )
    #                 ),
    #             "check": $sum([$gs?1:0,$ss?1:0,$sc?1:0])!=1 or
    #                      ($ss and $not(forStudySiteId in $sv.organizations.managedSites.id)) or
    #                      ($sc and $not(forStudyCohortId in $sv.**.cohorts.id))
    #           }
    #         )[check=true]

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00195: not yet implemented")
