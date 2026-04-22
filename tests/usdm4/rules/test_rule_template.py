"""Direct tests for RuleTemplate and ValidationLocation.

Covers the shared helpers used by every rule_ddf* module:
- ValidationLocation.__str__ (line 30)
- RuleTemplate.validate raises NotImplementedError (line 51)
- _ct_check code/decode mismatch branch (lines 119-126)
- _check_codelist raises CTException when codelist is None (line 139)
- _check_codelist raises CTException when terms are missing (line 144)
- _codes_and_decodes returns None, None when no terms (line 151)
"""

from unittest.mock import MagicMock

import pytest

from src.usdm4.rules.rule_template import RuleTemplate, ValidationLocation


def test_validation_location_str():
    loc = ValidationLocation(
        rule="DDF0001",
        rule_text="Sample rule",
        klass="Study",
        attribute="name",
        path="$.study.name",
    )
    s = str(loc)
    assert "DDF0001" in s
    assert "Sample rule" in s
    assert "Study.name" in s
    assert "$.study.name" in s


def test_validation_location_to_dict_and_headers():
    loc = ValidationLocation("R", "T", "K", "A", "P")
    assert loc.to_dict() == {
        "rule": "R",
        "rule_text": "T",
        "klass": "K",
        "attribute": "A",
        "path": "P",
    }
    assert ValidationLocation.headers() == [
        "rule",
        "rule_text",
        "klass",
        "attribute",
        "path",
    ]


def test_rule_template_validate_raises_not_implemented():
    rt = RuleTemplate("R001", RuleTemplate.ERROR, "rule text")
    with pytest.raises(NotImplementedError):
        rt.validate({})


def test_rule_template_result_initial_true():
    rt = RuleTemplate("R001", RuleTemplate.ERROR, "rule text")
    assert rt._result() is True
    assert rt.errors().count() == 0


def test_ct_check_code_decode_mismatch_raises_failure():
    """Exercise the mismatched code/decode branch (lines 118-124)."""
    rt = RuleTemplate("R002", RuleTemplate.ERROR, "mismatched code/decode")

    # codes=["A","B"], decodes=["DA","DB"]. Item has code="A" (index 0),
    # decode="DB" (index 1) — indexes differ, triggering the mismatch path.
    codelist = {
        "terms": [
            {"conceptId": "A", "preferredTerm": "DA"},
            {"conceptId": "B", "preferredTerm": "DB"},
        ]
    }

    ct = MagicMock()
    ct.klass_and_attribute.return_value = codelist

    data = MagicMock()
    data.instances_by_klass.return_value = [
        {"id": "i1", "status": {"code": "A", "decode": "DB"}}
    ]
    data.path_by_id.return_value = "$.study"

    ok = rt._ct_check({"data": data, "ct": ct}, "Study", "status")

    assert ok is False
    assert rt.errors().count() == 1


def test_ct_check_missing_attribute_raises_failure():
    rt = RuleTemplate("R003", RuleTemplate.ERROR, "missing attribute")

    codelist = {
        "terms": [
            {"conceptId": "A", "preferredTerm": "DA"},
        ]
    }
    ct = MagicMock()
    ct.klass_and_attribute.return_value = codelist

    data = MagicMock()
    # Instance has NO "status" attribute at all
    data.instances_by_klass.return_value = [{"id": "i1"}]
    data.path_by_id.return_value = "$.study"

    ok = rt._ct_check({"data": data, "ct": ct}, "Study", "status")
    assert ok is False
    assert rt.errors().count() == 1


def test_check_codelist_raises_when_codelist_missing():
    """Line 139: no codelist found for klass/attribute -> CTException."""
    rt = RuleTemplate("R004", RuleTemplate.ERROR, "missing codelist")
    ct = MagicMock()
    ct.klass_and_attribute.return_value = None
    with pytest.raises(RuleTemplate.CTException) as ex:
        rt._check_codelist(ct, "Study", "status")
    assert "Failed to find code list" in str(ex.value)


def test_check_codelist_raises_when_terms_missing():
    """Line 144: codelist present but terms empty -> CTException."""
    rt = RuleTemplate("R005", RuleTemplate.ERROR, "missing terms")
    ct = MagicMock()
    ct.klass_and_attribute.return_value = {"terms": []}
    with pytest.raises(RuleTemplate.CTException) as ex:
        rt._check_codelist(ct, "Study", "status")
    assert "Failed to find terms" in str(ex.value)


def test_codes_and_decodes_returns_none_pair_when_no_terms():
    """Line 151: empty/absent terms returns (None, None)."""
    rt = RuleTemplate("R006", RuleTemplate.ERROR, "no terms")
    codes, decodes = rt._codes_and_decodes({"terms": []})
    assert codes is None and decodes is None
    codes, decodes = rt._codes_and_decodes({})
    assert codes is None and decodes is None


def test_find_index_returns_index_or_none():
    rt = RuleTemplate("R007", RuleTemplate.ERROR, "find index")
    assert rt._find_index(["a", "b", "c"], "b") == 1
    assert rt._find_index(["a", "b", "c"], "missing") is None
