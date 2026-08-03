# MANUAL: do not regenerate
#
# Per StudyVersion: every Code beneath has (codeSystem,
# codeSystemVersion). For each codeSystem, distinct codeSystemVersion
# count should be 1. When >1, flag ONE failure per (codeSystem,
# codeSystemVersion) group, recording how many Code instances use that
# version and pointing at the first one as a representative path.
# Matches CORE-000808's `$record_count` semantics — one row per
# version-group rather than one per Code instance (which drowned the
# report; 623 rows on the sample vs CORE's 2).
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
            sv_id = sv.get("id")
            # {codeSystem: {codeSystemVersion: [Code instance, ...]}}
            by_system_version: dict = defaultdict(lambda: defaultdict(list))
            for code_inst in data.instances_by_klass("Code"):
                code_sv = data.parent_by_klass(code_inst.get("id"), "StudyVersion")
                if code_sv is None or code_sv.get("id") != sv_id:
                    continue
                cs = code_inst.get("codeSystem")
                csv = code_inst.get("codeSystemVersion")
                if cs and csv:
                    by_system_version[cs][csv].append(code_inst)

            for cs, versions_map in by_system_version.items():
                if len(versions_map) <= 1:
                    continue
                all_versions = sorted(versions_map.keys())
                # Emit one failure per version group — representative instance
                # + count of codes using that version. Avoids the 623-rows
                # per-Code blow-up.
                for csv, code_insts in versions_map.items():
                    representative = code_insts[0]
                    self._add_failure(
                        f"codeSystem {cs!r} has {len(code_insts)} Code(s) "
                        f"using codeSystemVersion {csv!r}; other versions in "
                        f"use within this StudyVersion: "
                        f"{[v for v in all_versions if v != csv]}",
                        "Code",
                        "codeSystem, codeSystemVersion",
                        data.path_by_id(representative["id"]),
                    )
        return self._result()
