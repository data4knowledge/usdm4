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


# ---------------------------------------------------------------------------
# _codes_and_decodes accepts BOTH preferredTerm and submissionValue
# ---------------------------------------------------------------------------
#
# CDISC publishes two labels for each codelist term: preferredTerm (NCI
# Thesaurus form) and submissionValue (SDTM/CDASH submission form).
# Sponsors legitimately encode either. Earlier versions of d4k only
# accepted preferredTerm and flagged perfectly valid submissionValue
# encodings as "Invalid decode". The cases below pin the wider behaviour.


def test_codes_and_decodes_returns_dict_for_decodes():
    """Shape contract: decodes is a {label: term_index} dict, not a list."""
    rt = RuleTemplate("R010", RuleTemplate.ERROR, "shape")
    codelist = {
        "terms": [
            {"conceptId": "C1", "preferredTerm": "P1", "submissionValue": "S1"},
            {"conceptId": "C2", "preferredTerm": "P2", "submissionValue": "S2"},
        ]
    }
    codes, decodes = rt._codes_and_decodes(codelist)
    assert codes == ["C1", "C2"]
    assert isinstance(decodes, dict)
    assert decodes == {"P1": 0, "S1": 0, "P2": 1, "S2": 1}


def test_codes_and_decodes_handles_term_with_only_preferred_term():
    """Backward compat — terms with no submissionValue (or null) still index by preferredTerm."""
    rt = RuleTemplate("R011", RuleTemplate.ERROR, "preferred only")
    codelist = {
        "terms": [
            {"conceptId": "C1", "preferredTerm": "P1"},
            {"conceptId": "C2", "preferredTerm": "P2", "submissionValue": None},
        ]
    }
    codes, decodes = rt._codes_and_decodes(codelist)
    assert codes == ["C1", "C2"]
    assert decodes == {"P1": 0, "P2": 1}


def test_codes_and_decodes_handles_term_with_only_submission_value():
    """Defensive — terms with no preferredTerm still index by submissionValue."""
    rt = RuleTemplate("R012", RuleTemplate.ERROR, "submission only")
    codelist = {
        "terms": [
            {"conceptId": "C1", "submissionValue": "S1"},
            {"conceptId": "C2", "preferredTerm": None, "submissionValue": "S2"},
        ]
    }
    codes, decodes = rt._codes_and_decodes(codelist)
    assert codes == ["C1", "C2"]
    assert decodes == {"S1": 0, "S2": 1}


def test_codes_and_decodes_does_not_include_synonyms():
    """Synonyms are deliberately excluded — we accept the two published labels only."""
    rt = RuleTemplate("R013", RuleTemplate.ERROR, "no synonyms")
    codelist = {
        "terms": [
            {
                "conceptId": "C54149",
                "preferredTerm": "Drug Company",
                "submissionValue": "Pharmaceutical Company",
                "synonyms": ["Pharma", "Drug Manufacturer"],
            }
        ]
    }
    codes, decodes = rt._codes_and_decodes(codelist)
    assert codes == ["C54149"]
    assert decodes == {"Drug Company": 0, "Pharmaceutical Company": 0}
    assert "Pharma" not in decodes
    assert "Drug Manufacturer" not in decodes


# ---------------------------------------------------------------------------
# _ct_check accepts decode whether it's preferredTerm or submissionValue
# ---------------------------------------------------------------------------


def _ct_with_c54149():
    """CT stub returning the real C188724/C54149 shape (preferredTerm and
    submissionValue diverge, which is precisely the case that motivated
    widening the check)."""
    ct = MagicMock()
    ct.klass_and_attribute.return_value = {
        "terms": [
            {
                "conceptId": "C54149",
                "preferredTerm": "Drug Company",
                "submissionValue": "Pharmaceutical Company",
            }
        ]
    }
    return ct


def test_ct_check_accepts_preferred_term_decode():
    rt = RuleTemplate("R020", RuleTemplate.ERROR, "preferred ok")
    data = MagicMock()
    data.instances_by_klass.return_value = [
        {"id": "i1", "type": {"code": "C54149", "decode": "Drug Company"}}
    ]
    data.path_by_id.return_value = "$.org"

    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is True
    assert rt.errors().count() == 0


def test_ct_check_accepts_submission_value_decode():
    """The regression case: C54149's submissionValue is 'Pharmaceutical Company',
    which is also what the project's own builder emits via
    cdisc_code('C54149', 'Pharmaceutical Company'). Previously rejected."""
    rt = RuleTemplate("R021", RuleTemplate.ERROR, "submission ok")
    data = MagicMock()
    data.instances_by_klass.return_value = [
        {"id": "i1", "type": {"code": "C54149", "decode": "Pharmaceutical Company"}}
    ]
    data.path_by_id.return_value = "$.org"

    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is True
    assert rt.errors().count() == 0


def test_ct_check_rejects_decode_that_is_neither():
    """A decode string that matches neither published label is still a failure."""
    rt = RuleTemplate("R022", RuleTemplate.ERROR, "neither")
    data = MagicMock()
    data.instances_by_klass.return_value = [
        {"id": "i1", "type": {"code": "C54149", "decode": "Pharma"}}
    ]
    data.path_by_id.return_value = "$.org"

    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is False
    assert rt.errors().count() == 1


def test_ct_check_mismatch_detected_when_code_from_one_term_decode_from_another():
    """The pair-mismatch check must still work after the dict change.

    code=C54149 (term 0) paired with decode='Study Registry' (term 1's
    preferredTerm) is a real mismatch — both label and code are valid in
    the codelist, but they're from different terms. The dict approach
    preserves this because each label resolves to its own term's index.
    """
    rt = RuleTemplate("R023", RuleTemplate.ERROR, "mismatch")
    ct = MagicMock()
    ct.klass_and_attribute.return_value = {
        "terms": [
            {
                "conceptId": "C54149",
                "preferredTerm": "Drug Company",
                "submissionValue": "Pharmaceutical Company",
            },
            {
                "conceptId": "C93453",
                "preferredTerm": "Study Registry",
                "submissionValue": "Clinical Study Registry",
            },
        ]
    }
    data = MagicMock()
    data.instances_by_klass.return_value = [
        {"id": "i1", "type": {"code": "C54149", "decode": "Study Registry"}}
    ]
    data.path_by_id.return_value = "$.org"

    ok = rt._ct_check({"data": data, "ct": ct}, "Organization", "type")
    assert ok is False
    assert rt.errors().count() == 1


def test_ct_check_mismatch_also_detected_when_decode_is_submission_value_of_other_term():
    """Same as above but the decode is the OTHER term's submissionValue
    (not preferredTerm). Still a mismatch — both labels resolve to
    different term indexes so code_index != decode_index."""
    rt = RuleTemplate("R024", RuleTemplate.ERROR, "submission mismatch")
    ct = MagicMock()
    ct.klass_and_attribute.return_value = {
        "terms": [
            {
                "conceptId": "C54149",
                "preferredTerm": "Drug Company",
                "submissionValue": "Pharmaceutical Company",
            },
            {
                "conceptId": "C93453",
                "preferredTerm": "Study Registry",
                "submissionValue": "Clinical Study Registry",
            },
        ]
    }
    data = MagicMock()
    data.instances_by_klass.return_value = [
        {"id": "i1", "type": {"code": "C54149", "decode": "Clinical Study Registry"}}
    ]
    data.path_by_id.return_value = "$.org"

    ok = rt._ct_check({"data": data, "ct": ct}, "Organization", "type")
    assert ok is False
    assert rt.errors().count() == 1
