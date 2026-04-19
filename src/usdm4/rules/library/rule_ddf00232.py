# MANUAL: do not regenerate
#
# For each ObservationalStudyDesign, studyPhase must be present and
# its AliasCode.standardCode.decode must equal "NOT APPLICABLE"
# (case-insensitive — CDISC preferred term is "Not Applicable" but
# the rule text upper-cases it).
from usdm4.rules.rule_template import RuleTemplate


NOT_APPLICABLE_DECODE = "NOT APPLICABLE"


def _phase_decode(design):
    phase = design.get("studyPhase")
    if not isinstance(phase, dict):
        return None
    standard = phase.get("standardCode")
    if not isinstance(standard, dict):
        return None
    return standard.get("decode")


class RuleDDF00232(RuleTemplate):
    """
    DDF00232: An observational study (including patient registries) is expected to have a study phase decode value of "NOT APPLICABLE".

    Applies to: ObservationalStudyDesign
    Attributes: studyPhase
    """

    def __init__(self):
        super().__init__(
            "DDF00232",
            RuleTemplate.WARNING,
            'An observational study (including patient registries) is expected to have a study phase decode value of "NOT APPLICABLE".',
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for design in data.instances_by_klass("ObservationalStudyDesign"):
            decode = _phase_decode(design)
            if decode is None:
                self._add_failure(
                    "ObservationalStudyDesign has no studyPhase decode",
                    "ObservationalStudyDesign",
                    "studyPhase",
                    data.path_by_id(design["id"]),
                )
                continue
            if decode.strip().upper() != NOT_APPLICABLE_DECODE:
                self._add_failure(
                    f"ObservationalStudyDesign studyPhase decode is {decode!r}, expected 'NOT APPLICABLE'",
                    "ObservationalStudyDesign",
                    "studyPhase",
                    data.path_by_id(design["id"]),
                )
        return self._result()
