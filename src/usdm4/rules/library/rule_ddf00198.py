# MANUAL: do not regenerate
#
# Build the set of StudyDefinitionDocumentVersion ids referenced from
# any StudyVersion.documentVersionIds or {Interventional,Observational}
# StudyDesign.documentVersionIds. Every SDDV not in that set fails.
from usdm4.rules.rule_template import RuleTemplate


REFERRING_CLASSES = [
    "StudyVersion",
    "InterventionalStudyDesign",
    "ObservationalStudyDesign",
]


class RuleDDF00198(RuleTemplate):
    """
    DDF00198: Each study definition document version is expected to be referenced by either a study version or a study design.

    Applies to: StudyDefinitionDocumentVersion (referenced from StudyVersion or StudyDesign)
    Attributes: documentVersionIds
    """

    def __init__(self):
        super().__init__(
            "DDF00198",
            RuleTemplate.WARNING,
            "Each study definition document version is expected to be referenced by either a study version or a study design.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        referenced_ids: set = set()
        for klass in REFERRING_CLASSES:
            for instance in data.instances_by_klass(klass):
                for dv_id in instance.get("documentVersionIds") or []:
                    if dv_id:
                        referenced_ids.add(dv_id)
        for sddv in data.instances_by_klass("StudyDefinitionDocumentVersion"):
            if sddv.get("id") not in referenced_ids:
                self._add_failure(
                    "StudyDefinitionDocumentVersion is not referenced by any StudyVersion or StudyDesign",
                    "StudyDefinitionDocumentVersion",
                    "documentVersionIds",
                    data.path_by_id(sddv["id"]),
                )
        return self._result()
