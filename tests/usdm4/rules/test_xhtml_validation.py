"""Tests for the shared USDM-XHTML validator."""

from usdm4.rules.xhtml_validation import (
    XhtmlValidator,
    get_validator,
)


def test_singleton_returns_same_instance():
    a = get_validator()
    b = get_validator()
    assert a is b


def test_none_and_empty_return_no_errors():
    v = XhtmlValidator()
    assert v.validate(None) == []
    assert v.validate("") == []
    assert v.validate("   \n   ") == []


def test_non_string_input_returns_single_error():
    v = XhtmlValidator()
    errs = v.validate(123)
    assert len(errs) == 1
    assert "not a string" in errs[0].message


def test_valid_fragment_returns_no_errors():
    v = XhtmlValidator()
    assert v.validate("<p>Valid paragraph</p>") == []


def test_valid_list_with_nested_p_in_li():
    """<p> is fine inside <li>, just not inside <ul> directly."""
    v = XhtmlValidator()
    text = "<ul><li><p>nested</p></li></ul>"
    assert v.validate(text) == []


def test_p_directly_inside_ul_fails():
    v = XhtmlValidator()
    text = "<ul><p>wrong</p><li>ok</li></ul>"
    errs = v.validate(text)
    assert errs, "expected schema error"
    msg = errs[0].message
    # Schema reports the element name and what was expected.
    assert "p" in msg and "li" in msg


def test_parse_error_for_broken_markup():
    v = XhtmlValidator()
    errs = v.validate("<p>unclosed")
    assert errs, "expected parse error"
    assert errs[0].line is not None


def test_parse_error_for_bad_attribute():
    v = XhtmlValidator()
    errs = v.validate("<p class=>missing value</p>")
    assert errs


def test_usdm_ref_element_is_allowed():
    """The USDM-XHTML schema adds <usdm:ref> as an allowed extension."""
    v = XhtmlValidator()
    text = '<p>See <usdm:ref klass="X" id="Y" attribute="name"/></p>'
    assert v.validate(text) == []


def test_usdm_tag_element_is_allowed():
    v = XhtmlValidator()
    text = '<p><usdm:tag name="NAME"/></p>'
    assert v.validate(text) == []
