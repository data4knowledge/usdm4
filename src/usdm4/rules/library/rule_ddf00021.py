from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00021(RuleTemplate):
    """
    DDF00021: An instance of a class must not refer to itself as its previous instance.

    Applies to: StudyEpoch, Encounter, Activity, NarrativeContent, EligibilityCriterion, StudyAmendment
    Attributes: previous
    """

    def __init__(self):
        super().__init__(
            "DDF00021",
            RuleTemplate.ERROR,
            "An instance of a class must not refer to itself as its previous instance.",
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00021: not yet implemented")
