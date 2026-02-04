from typing import Union, List, Literal
from .api_base_model import ApiBaseModelWithIdNameLabelAndDesc
from .study_amendment_reason import StudyAmendmentReason
from .study_change import StudyChange
from .study_amendment_impact import StudyAmendmentImpact
from .geographic_scope import GeographicScope
from .subject_enrollment import SubjectEnrollment
from .governance_date import GovernanceDate
from .comment_annotation import CommentAnnotation
from .extension import ExtensionAttribute

SI_EXT_URL = (
    "www.d4k.dk/usdm/extensions/003"  # Site identifier scope. An array of extensions.
)


class StudyAmendment(ApiBaseModelWithIdNameLabelAndDesc):
    number: str
    summary: str
    primaryReason: StudyAmendmentReason
    secondaryReasons: List[StudyAmendmentReason] = []
    changes: List[StudyChange] = []  # Not in API
    impacts: List[StudyAmendmentImpact] = []
    geographicScopes: List[GeographicScope]
    enrollments: List[SubjectEnrollment] = []
    dateValues: List[GovernanceDate] = []
    previousId: Union[str, None] = None
    notes: List[CommentAnnotation] = []
    instanceType: Literal["StudyAmendment"]

    def site_identifier_scopes(self) -> list[str]:
        ext: ExtensionAttribute = self.get_extension(SI_EXT_URL)
        return [x.valueString for x in ext.extensionAttributes] if ext else []

    def site_identifier_scopes_as_text(self) -> str:
        return (",").join(self.site_identifier_scopes())

    def primary_reason_as_text(self) -> str:
        return self.primaryReason.reason_as_text()

    def primary_other_reason_as_text(self) -> str:
        return self.primaryReason.other_reason_as_text()

    def secondary_reason_as_text(self) -> str:
        return (
            self.secondaryReasons[0].reason_as_text()
            if len(self.secondaryReasons) > 0
            else ""
        )

    def secondary_other_reason_as_text(self) -> str:
        return (
            self.secondaryReasons[0].other_reason_as_text()
            if len(self.secondaryReasons) > 0
            else ""
        )

    def is_global(self) -> bool:
        for scope in self.geographicScopes:
            if scope.type.code == "C68846":
                return True
        return False
