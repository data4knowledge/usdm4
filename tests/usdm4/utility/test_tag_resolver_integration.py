"""Integration tests for TagResolver over a real USDM file, via the two
public access routes: USDM4.tag_resolver() and Builder.data_store."""

from simple_error_log.errors import Errors
from usdm4 import USDM4, TagResolver

FILE = "tests/usdm4/test_files/integration/sample_usdm_7.json"


def test_facade_tag_resolver_recursive_tag_and_ref():
    """usdm:tag resolves through the dictionary's parameterMaps to a
    usdm:ref, which recursively resolves to the referenced attribute value
    (min_age -> Quantity_9.value = 18.0)."""
    errors = Errors()
    resolver = USDM4().tag_resolver(FILE, errors)
    instance = {
        "id": "EligibilityCriterionItem_X",
        "dictionaryId": "SyntaxTemplateDictionary_1",
    }
    result = resolver.translate(instance, '<p>Age <usdm:tag name="min_age"/></p>')
    assert errors.error_count() == 0
    assert "usdm:tag" not in result
    assert "usdm:ref" not in result
    assert result == "<p>Age 18.0</p>"


def test_facade_tag_resolver_plain_text_untouched():
    errors = Errors()
    resolver = USDM4().tag_resolver(FILE, errors)
    text = "<p>No special tags here</p>"
    assert resolver.translate({"id": "X"}, text) == text
    assert errors.error_count() == 0


def test_facade_tag_resolver_rich_content_not_escaped():
    """A usdm:ref pointing at an attribute that itself contains XHTML (and a
    nested usdm:tag) must be inserted as markup, not escaped text — the
    output is destined for rendered documents (usdm4_protocol / usdm4)."""
    errors = Errors()
    resolver = USDM4().tag_resolver(FILE, errors)
    instance = {
        "id": "X",
        "dictionaryId": "SyntaxTemplateDictionary_1",
    }
    text = (
        '<div><usdm:ref klass="EligibilityCriterionItem" '
        'id="EligibilityCriterionItem_2" attribute="text"></usdm:ref></div>'
    )
    result = resolver.translate(instance, text)
    assert errors.error_count() == 0
    assert "&lt;" not in result  # markup, not escaped
    assert "<p>" in result  # the referenced XHTML survives
    assert "usdm:" not in result  # its nested usdm:tag resolved too


def test_stray_usdm_macro_warns_and_is_left_in_place():
    """usdm:macro is authoring-only (expanded by usdm4_excel at import) and
    should never reach USDM content: the resolver warns and leaves it."""
    errors = Errors()
    resolver = USDM4().tag_resolver(FILE, errors)
    instance = {"id": "X", "dictionaryId": "SyntaxTemplateDictionary_1"}
    result = resolver.translate(
        instance,
        '<p>Age <usdm:tag name="min_age"/> <usdm:macro id="note" text="hi"/></p>',
    )
    assert "Age 18.0" in result
    assert "usdm:macro" in result  # left unresolved, visibly
    assert errors.error_count() == 0
    warnings = [item["message"] for item in errors.to_dict(errors.WARNING)]
    assert any("Unexpanded usdm:macro" in w for w in warnings)


def test_builder_data_store_property():
    """Builder.data_store is None before seed() and exposes the store after,
    usable to build a TagResolver directly."""
    errors = Errors()
    builder = USDM4().builder(errors)
    assert builder.data_store is None
    builder.seed(FILE)
    assert builder.data_store is not None
    resolver = TagResolver(builder.data_store, errors)
    instance = {
        "id": "EligibilityCriterionItem_X",
        "dictionaryId": "SyntaxTemplateDictionary_1",
    }
    result = resolver.translate(instance, '<usdm:tag name="max_age"/>')
    assert "usdm:tag" not in result
    assert errors.error_count() == 0
