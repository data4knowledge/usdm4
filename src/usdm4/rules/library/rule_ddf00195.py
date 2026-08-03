# MANUAL: do not regenerate
#
# Exactly one of the three "for..." slots must be populated on a
# SubjectEnrollment, AND any referenced id must resolve:
#   forStudySiteId  → must point to an existing Organization-owned
#                     managedSite id
#   forStudyCohortId → must point to an existing StudyCohort id
# `forGeographicScope` is an embedded object, so "existence" is just
# non-None presence.
from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00195(RuleTemplate):
    """
    DDF00195: Each study enrollment must apply to either a geographic scope, a study site, or a study cohort.

    Applies to: SubjectEnrollment
    Attributes: forGeographicScope, forStudySiteId, forStudyCohortId
    """

    def __init__(self):
        super().__init__(
            "DDF00195",
            RuleTemplate.ERROR,
            "Each study enrollment must apply to either a geographic scope, a study site, or a study cohort.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        # Build id lookup sets once
        site_ids = {
            s.get("id")
            for s in data.instances_by_klass("ManagedSite")
            if isinstance(s, dict)
        }
        cohort_ids = {
            c.get("id")
            for c in data.instances_by_klass("StudyCohort")
            if isinstance(c, dict)
        }
        for enrollment in data.instances_by_klass("SubjectEnrollment"):
            gs = enrollment.get("forGeographicScope")
            site_id = enrollment.get("forStudySiteId")
            cohort_id = enrollment.get("forStudyCohortId")
            slots = [bool(gs), bool(site_id), bool(cohort_id)]
            if sum(slots) != 1:
                self._add_failure(
                    f"SubjectEnrollment must reference exactly one of forGeographicScope / forStudySiteId / forStudyCohortId (found {sum(slots)})",
                    "SubjectEnrollment",
                    "forGeographicScope, forStudySiteId, forStudyCohortId",
                    data.path_by_id(enrollment["id"]),
                )
                continue
            if site_id and site_id not in site_ids:
                self._add_failure(
                    f"SubjectEnrollment.forStudySiteId {site_id!r} does not resolve to an existing ManagedSite",
                    "SubjectEnrollment",
                    "forStudySiteId",
                    data.path_by_id(enrollment["id"]),
                )
            if cohort_id and cohort_id not in cohort_ids:
                self._add_failure(
                    f"SubjectEnrollment.forStudyCohortId {cohort_id!r} does not resolve to an existing StudyCohort",
                    "SubjectEnrollment",
                    "forStudyCohortId",
                    data.path_by_id(enrollment["id"]),
                )
        return self._result()
