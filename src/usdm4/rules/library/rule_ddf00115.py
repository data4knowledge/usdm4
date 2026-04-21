# MANUAL: do not regenerate
#
# Every StudyVersion must have at least one StudyTitle whose
# type.code is C207616 ("Official Study Title"). Titles live
# embedded under StudyVersion.titles.
from usdm4.rules.rule_template import RuleTemplate


OFFICIAL_STUDY_TITLE_CODE = "C207616"


class RuleDDF00115(RuleTemplate):
    """
    DDF00115: Every study version must have a title of type "Official Study Title".

    Applies to: StudyVersion
    Attributes: titles
    """

    def __init__(self):
        super().__init__(
            "DDF00115",
            RuleTemplate.ERROR,
            'Every study version must have a title of type "Official Study Title".',
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for sv in data.instances_by_klass("StudyVersion"):
            titles = sv.get("titles") or []
            has_official = any(
                isinstance(t, dict)
                and isinstance(t.get("type"), dict)
                and t["type"].get("code") == OFFICIAL_STUDY_TITLE_CODE
                for t in titles
            )
            if not has_official:
                self._add_failure(
                    "StudyVersion has no title of type 'Official Study Title' (C207616)",
                    "StudyVersion",
                    "titles",
                    data.path_by_id(sv["id"]),
                )
        return self._result()
