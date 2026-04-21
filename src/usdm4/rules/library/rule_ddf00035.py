# MANUAL: do not regenerate
#
# Across all Code instances, for each (codeSystem, codeSystemVersion),
# enforce a 1:1 mapping between `code` and `decode`. Uses two
# dict-of-sets (same idiom as DDF00196): code→decodes and
# decode→codes. Flags any Code whose (codeSystem, codeSystemVersion,
# code) shares decodes with >1 value, or whose (codeSystem,
# codeSystemVersion, decode) shares codes with >1.
from collections import defaultdict

from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00035(RuleTemplate):
    """
    DDF00035: Within a code system and corresponding version, a one-to-one relationship between code and decode is expected.

    Applies to: Code
    Attributes: code, decode
    """

    def __init__(self):
        super().__init__(
            "DDF00035",
            RuleTemplate.WARNING,
            "Within a code system and corresponding version, a one-to-one relationship between code and decode is expected.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        code_to_decodes: dict = defaultdict(set)
        decode_to_codes: dict = defaultdict(set)
        for code_inst in data.instances_by_klass("Code"):
            cs = code_inst.get("codeSystem")
            csv = code_inst.get("codeSystemVersion")
            code = code_inst.get("code")
            decode = code_inst.get("decode")
            if None in (cs, csv, code, decode):
                continue
            code_to_decodes[(cs, csv, code)].add(decode)
            decode_to_codes[(cs, csv, decode)].add(code)
        for code_inst in data.instances_by_klass("Code"):
            cs = code_inst.get("codeSystem")
            csv = code_inst.get("codeSystemVersion")
            code = code_inst.get("code")
            decode = code_inst.get("decode")
            if None in (cs, csv, code, decode):
                continue
            if len(code_to_decodes[(cs, csv, code)]) > 1 or len(decode_to_codes[(cs, csv, decode)]) > 1:
                self._add_failure(
                    f"Code {code!r}/{decode!r} participates in a non-1:1 mapping within {cs}@{csv}",
                    "Code",
                    "code, decode",
                    data.path_by_id(code_inst["id"]),
                )
        return self._result()
