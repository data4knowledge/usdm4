from usdm4.rules.rule_template import RuleTemplate


class RuleDDF00258(RuleTemplate):
    """
    DDF00258: A study design is not expected to have more than one of the following characteristics: "Randomized", "Stratification", "Stratified Randomisation".

    Applies to: InterventionalStudyDesign, ObservationalStudyDesign
    Attributes: characteristics
    """

    def __init__(self):
        super().__init__(
            "DDF00258",
            RuleTemplate.WARNING,
            'A study design is not expected to have more than one of the following characteristics: "Randomized", "Stratification", "Stratified Randomisation".',
        )

    # TODO: implement. LOW_CUSTOM: JSONata translator did not match a known pattern
    # Reference — CORE JSONata condition (semantics, not executed):
    #     study.versions.studyDesigns[$count(characteristics[code in ["C46079","C25689","C147145"]])>1].
    #       {
    #         "instanceType": instanceType,
    #         "id": id,
    #         "path": _path,
    #         "name": name,
    #         "characteristics": "["&$join(characteristics[code in ["C46079","C25689","C147145"]].$.(id&": "&decode&" ("&code&")"),"; ")&"]"
    #       }

    def validate(self, config: dict) -> bool:
        raise NotImplementedError("DDF00258: not yet implemented")
