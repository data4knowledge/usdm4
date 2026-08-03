# MANUAL: do not regenerate
#
# NarrativeContentItem.text must be valid USDM-XHTML. Previous
# implementation used `xml.etree.ElementTree` which only checks
# well-formedness; CORE-001069 additionally validates against the
# USDM-XHTML 1.0 XML Schema, catching structural violations like
# `<p>` as a direct child of `<ul>`. The shared `xhtml_validation`
# module uses lxml + the bundled schema to match CORE's semantics.
from usdm4.rules.rule_template import RuleTemplate
from usdm4.rules.xhtml_validation import get_validator


class RuleDDF00187(RuleTemplate):
    """
    DDF00187: Narrative content item text is expected to be HTML formatted.

    Applies to: NarrativeContentItem
    Attributes: text
    """

    def __init__(self):
        super().__init__(
            "DDF00187",
            RuleTemplate.WARNING,
            "Narrative content item text is expected to be HTML formatted.",
        )

    def validate(self, config: dict) -> bool:
        data = config["data"]
        validator = get_validator()
        for item in data.instances_by_klass("NarrativeContentItem"):
            text = item.get("text")
            if not isinstance(text, str) or text.strip() == "":
                continue
            errors = validator.validate(text)
            if not errors:
                continue
            # One failure per instance, summarising the first few schema
            # / parse errors. Matches CORE-001069's granularity (one
            # finding per NCI rather than one per underlying XHTML
            # error).
            summary = "; ".join(
                f"line {e.line}: {e.message[:160]}" if e.line else e.message[:160]
                for e in errors[:3]
            )
            if len(errors) > 3:
                summary += f"; ... and {len(errors) - 3} more"
            self._add_failure(
                f"NarrativeContentItem.text is not valid USDM-XHTML — {summary}",
                "NarrativeContentItem",
                "text",
                data.path_by_id(item["id"]),
            )
        return self._result()
