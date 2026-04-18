from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00196(RuleTemplate):
    """
    DDF00196: There must be a one-to-one relationship between referenced section number and title within a study amendment.

    Applies to: DocumentContentReference
    Attributes: sectionNumber, sectionTitle
    """

    def __init__(self):
        super().__init__(
            "DDF00196",
            RuleTemplate.ERROR,
            "There must be a one-to-one relationship between referenced section number and title within a study amendment.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study@$s.
    #       $s.versions@$sv.
    #         $sv.amendments@$a.
    #           $a.changes@$sc.
    #             $sc.changedSections.
    #               (
    #                 $this:=$;
    #                 $t4n:=$distinct($a.changes.changedSections[sectionNumber = $this.sectionNumber and appliesToId = $this.appliesToId].sectionTitle)~>$sort;
    #                 $n4t:=$distinct($a.changes.changedSections[sectionTitle = $this.sectionTitle and appliesToId = $this.appliesToId].sectionNumber)~>$sort;
    #                 {
    #                   "instanceType": instanceType,
    #                   "id": id,
    #                   "path": _path,
    #                   "StudyAmendment.id": $a.id,
    #                   "StudyAmendment.name": $a.name,
    #                   "StudyChange.id": $sc.id,
    #                   "StudyChange.name": $sc.name,
    #                   "appliesToId": appliesToId &": "&
    #                     (
    #                       appliesToId in $s.documentedBy.id
    #                       ? $s.documentedBy[id=$this.appliesToId].name
    #                       : "Invalid appliesToId"
    #                     ),
    #                   "sectionNumber": sectionNumber,
    #                   "n4t": "["&$join($n4t,"; ")&"]",
    #                   "sectionTitle": sectionTitle,
    #                   "t4n": "["&$join($t4n,"; ")&"]",
    #                   "check": ($count($t4n)!=1 or $count($n4t)!=1)
    #                 }
    #               )[check=true] ~>
    #               $sort(function($l,$r)
    #                 {
    #                     $l.`StudyAmendment.id` >= $r.`StudyAmendment.id` and
    #                     $l.appliesToId >= $r.appliesToId and
    #                     $l.n4t >= $r.n4t and
    #                     $l.t4n > $r.t4n
    #                 }
    #               )

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00196: not yet implemented")
