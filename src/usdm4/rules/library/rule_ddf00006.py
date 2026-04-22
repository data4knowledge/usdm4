# MANUAL: do not regenerate
#
# All-or-nothing on Timing window attributes: if any of windowLabel /
# windowLower / windowUpper is specified, all three must be. Both
# "truly absent" (missing key) and "empty string / empty dict" count
# as not specified. windowLower/windowUpper are typically embedded
# Duration objects — empty dict or null → not specified.
from usdm4.rules.rule_template import RuleTemplate


WINDOW_ATTRS = ["windowLabel", "windowLower", "windowUpper"]


def _is_specified(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


class RuleDDF00006(RuleTemplate):
    """
    DDF00006: Timing windows must be fully defined, if one of the window attributes (i.e., window label, window lower, and window upper) is defined then all must be specified.

    Applies to: Timing
    Attributes: windowLabel, windowLower, windowUpper
    """

    def __init__(self):
        super().__init__(
            "DDF00006",
            RuleTemplate.ERROR,
            "Timing windows must be fully defined, if one of the window attributes (i.e., window label, window lower, and window upper) is defined then all must be specified.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for timing in data.instances_by_klass("Timing"):
            specified = [
                attr for attr in WINDOW_ATTRS if _is_specified(timing.get(attr))
            ]
            # If any are set, all three must be set
            if specified and len(specified) < len(WINDOW_ATTRS):
                missing = [a for a in WINDOW_ATTRS if a not in specified]
                self._add_failure(
                    f"Timing has partial window definition — set: {specified}, missing: {missing}",
                    "Timing",
                    ", ".join(WINDOW_ATTRS),
                    data.path_by_id(timing["id"]),
                )
        return self._result()
