# MANUAL: do not regenerate
#
# Window-on-anchor-timing check. Two problems with the previous version
# surfaced by the protocol_corpus run (n=234):
#
# 1) Filter mismatch. The previous body matched Timings via
#    `type.decode == "Fixed Reference"`, but the corpus data uses the
#    full SDTM PT `"Fixed Reference Timing Type"` (code C201358). The
#    filter never matched anything, so the rule reported 0 findings on
#    every file while CORE caught 103 violations. Now matched by code.
#
# 2) Missing attribute. The docstring lists windowLabel as one of the
#    attributes the rule applies to, but the previous body only checked
#    windowLower and windowUpper. CORE flagged exclusively on
#    windowLabel in this corpus (windowLower/Upper are always empty
#    strings or absent on the affected timings). Adding windowLabel
#    closes the gap.
#
# Empty-string semantics: CORE does not treat an empty-string value as
# "defined" — there are 131 files in the corpus where a Fixed Reference
# Timing has windowLower="" / windowUpper="" but no truthy windowLabel,
# and CORE does not flag them. We mirror that by using `bool(value)`
# rather than `value is not None`.
from usdm4.rules.rule_template import RuleTemplate


_FIXED_REFERENCE_CODE = "C201358"

# (attribute name on Timing, message text) pairs that the rule checks.
_WINDOW_ATTRIBUTES = (
    ("windowLabel", "Window label defined for anchor timing"),
    ("windowLower", "Window lower defined for anchor timing"),
    ("windowUpper", "Window upper defined for anchor timing"),
)


class RuleDDF00025(RuleTemplate):
    """
    DDF00025: A window must not be defined for an anchor timing (i.e., type is "Fixed Reference").

    Applies to: Timing
    Attributes: windowLabel, windowLower, windowUpper
    """

    def __init__(self):
        super().__init__(
            "DDF00025",
            RuleTemplate.ERROR,
            'A window must not be defined for an anchor timing (i.e., type is "Fixed Reference").',
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for item in data.instances_by_klass("Timing"):
            type_block = item.get("type")
            if not isinstance(type_block, dict):
                continue
            if type_block.get("code") != _FIXED_REFERENCE_CODE:
                continue
            path = data.path_by_id(item["id"])
            for attr, message in _WINDOW_ATTRIBUTES:
                if bool(item.get(attr)):
                    self._add_failure(message, "Timing", attr, path)
        return self._result()
