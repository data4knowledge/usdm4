# MANUAL: do not regenerate
#
# Per StudyVersion: every Code beneath has (codeSystem,
# codeSystemVersion). For each codeSystem, distinct codeSystemVersion
# count should be 1. When >1, flag each offending Code.
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00073(RuleTemplate):
    """
    DDF00073: Only one version of any code system is expected to be used within a study version.

    Applies to: Code (scoped within each StudyVersion)
    Attributes: codeSystem, codeSystemVersion
    """

    def __init__(self):
        super().__init__(
            "DDF00073",
            RuleTemplate.WARNING,
            "Only one version of any code system is expected to be used within a study version.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            # Collect every Code descendant of this StudyVersion.
            codes_by_system: dict = defaultdict(
                list
            )  # codeSystem -> list of (version, code instance)
            sv_id = sv.get("id")
            # Iterate all Codes, filter by ancestor StudyVersion.
            for code_inst in data.instances_by_klass("Code"):
                code_sv = data.parent_by_klass(code_inst.get("id"), "StudyVersion")
                if code_sv is None or code_sv.get("id") != sv_id:
                    continue
                cs = code_inst.get("codeSystem")
                csv = code_inst.get("codeSystemVersion")
                if cs and csv:
                    codes_by_system[cs].append((csv, code_inst))
            for cs, entries in codes_by_system.items():
                versions = {v for v, _ in entries}
                if len(versions) > 1:
                    for csv, code_inst in entries:
                        self._add_failure(
                            f"Multiple codeSystemVersion values in use for {cs!r}: {sorted(versions)}",
                            "Code",
                            "codeSystem, codeSystemVersion",
                            data.path_by_id(code_inst["id"]),
                        )
        return self._result()
