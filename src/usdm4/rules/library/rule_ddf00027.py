from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00027(RuleTemplate):
    """
    DDF00027: To ensure consistent ordering, the same instance must not be referenced more than once as previous or next.

    Applies to: Activity, EligibilityCriterion, Encounter, NarrativeContent, StudyEpoch
    Attributes: previous, next
    """

    def __init__(self):
        super().__init__(
            "DDF00027",
            RuleTemplate.ERROR,
            "To ensure consistent ordering, the same instance must not be referenced more than once as previous or next.",
        )

    # TODO: implement. HIGH_UNIQUE_WITHIN_SCOPE without scope info — ambiguous (global vs per-parent vs intra-attribute). Review rule text.
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00027: not yet implemented")
