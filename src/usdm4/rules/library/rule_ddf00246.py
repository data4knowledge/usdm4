# MANUAL: do not regenerate
#
# Extract every <usdm:tag name="xxx"/> out of each instance's `text`
# field. For each name, check it is present as a `tag` value in
# some ParameterMap under the Dictionary referenced by the instance's
# `dictionaryId`. Missing tag / missing dictionary / missing
# dictionaryId all fail.
import re

from usdm4.rules.rule_template import RuleTemplate


SCOPE_CLASSES = [
    "EligibilityCriterionItem",
    "Characteristic",
    "Condition",
    "Objective",
    "Endpoint",
    "IntercurrentEvent",
]

# <usdm:tag name="xxx"/> or <usdm:tag name="xxx"></usdm:tag>. Name
# must be word chars per the CORE regex.
TAG_NAME_RE = re.compile(r'<usdm:tag\b[^>]*\bname="(\w+)"[^>]*(?:/>|>\s*</usdm:tag>)')


class RuleDDF00246(RuleTemplate):
    """
    DDF00246: Any parameter name referenced in a tag in the text should be specified in the data dictionary parameter maps.

    Applies to: EligibilityCriterionItem, Characteristic, Condition, Objective, Endpoint, IntercurrentEvent
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00246",
            RuleTemplate.ERROR,
            "Any parameter name referenced in a tag in the text should be specified in the data dictionary parameter maps.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        for klass in SCOPE_CLASSES:
            for instance in data.instances_by_klass(klass):
                text = instance.get("text")
                if not isinstance(text, str) or "<usdm:tag" not in text:
                    continue
                tag_names = TAG_NAME_RE.findall(text)
                if not tag_names:
                    continue
                dictionary_id = instance.get("dictionaryId")
                if not dictionary_id:
                    self._add_failure(
                        f"{klass}.text contains <usdm:tag name=...> but no dictionaryId is set",
                        klass,
                        "text, dictionaryId",
                        data.path_by_id(instance["id"]),
                    )
                    continue
                dictionary = data.instance_by_id(dictionary_id)
                if not isinstance(dictionary, dict):
                    self._add_failure(
                        f"{klass}.dictionaryId {dictionary_id!r} does not resolve to a Dictionary",
                        klass,
                        "dictionaryId",
                        data.path_by_id(instance["id"]),
                    )
                    continue
                valid_tags = {
                    pm.get("tag")
                    for pm in dictionary.get("parameterMaps") or []
                    if isinstance(pm, dict) and pm.get("tag")
                }
                for name in tag_names:
                    if name not in valid_tags:
                        self._add_failure(
                            f"{klass}.text references parameter name {name!r} not found in Dictionary {dictionary_id!r}",
                            klass,
                            "text",
                            data.path_by_id(instance["id"]),
                        )
        return self._result()
