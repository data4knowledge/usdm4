"""Tests for RuleTemplate and ValidationLocation.

After the predicate-consolidation refactor (see project memory
``project_m11_sdtm_phase_code_tension`` and feedback memory
``feedback_missing_codelist_must_raise``), RuleTemplate._ct_check
delegates membership/match to Library.find_in_codelist. The internal
helpers (_check_codelist, _codes_and_decodes, _find_index) are gone.

These tests exercise _ct_check through a shared FakeCT stub that
mirrors the Library predicate contract — including raising
MissingCodelistError when the codelist is unknown or has no terms.
"""

from unittest.mock import MagicMock

import pytest

from usdm4.ct.cdisc.library import MissingCodelistError
from usdm4.rules.rule_template import RuleTemplate, ValidationLocation

from tests.usdm4.rules.ct_helpers import FakeCT


# ---------------------------------------------------------------------------
# ValidationLocation
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# RuleTemplate base behaviour
# ---------------------------------------------------------------------------


def test_rule_template_validate_raises_not_implemented():
    rt = RuleTemplate("R001", RuleTemplate.ERROR, "rule text")
    with pytest.raises(NotImplementedError):
        rt.validate({})


def test_rule_template_result_initial_true():
    rt = RuleTemplate("R001", RuleTemplate.ERROR, "rule text")
    assert rt._result() is True
    assert rt.errors().count() == 0


# ---------------------------------------------------------------------------
# _ct_check — codelist resolution
#
# When ct_config.yaml doesn't map (klass, attribute) to a conceptId,
# the rule is registered against an unmapped attribute — a config flaw
# distinct from "codelist not loaded". CTException stays the signal for
# this case; MissingCodelistError covers the loaded-but-not-in-cache case.
# ---------------------------------------------------------------------------


def test_ct_check_raises_ct_exception_when_klass_attribute_unmapped():
    rt = RuleTemplate("R100", RuleTemplate.ERROR, "no mapping")
    # FakeCT with no klass_attribute_map → klass_and_attribute returns None.
    ct = FakeCT({})
    data = MagicMock()
    with pytest.raises(RuleTemplate.CTException, match="Failed to find code list"):
        rt._ct_check({"data": data, "ct": ct}, "Study", "status")


def test_ct_check_propagates_missing_codelist_error_when_codelist_absent():
    """klass_and_attribute returns None for an unmapped pair (above).
    But if the mapping exists yet the codelist isn't loaded into the
    Library, klass_and_attribute itself raises MissingCodelistError —
    see Library.klass_and_attribute, which deliberately splits "no
    mapping" (None return) from "mapping resolves but codelist not in
    cache" (MissingCodelistError). _ct_check must propagate the latter
    so the operator sees a stale-cache config flaw, not the misleading
    "Failed to find code list" message that the unmapped-attribute
    case carries."""
    rt = RuleTemplate("R101", RuleTemplate.ERROR, "predicate raises")
    ct = MagicMock()
    ct.klass_and_attribute.side_effect = MissingCodelistError(
        "Codelist 'C_GHOST' is not loaded in the CT cache"
    )
    data = MagicMock()
    data.instances_by_klass.return_value = [
        {"id": "i1", "status": {"code": "X", "decode": "Y"}}
    ]
    data.path_by_id.return_value = "$.study"
    with pytest.raises(MissingCodelistError, match="not loaded"):
        rt._ct_check({"data": data, "ct": ct}, "Study", "status")


# ---------------------------------------------------------------------------
# _ct_check — happy-path behaviour
# ---------------------------------------------------------------------------


def _ct_with_c54149():
    """FakeCT carrying the C54149 ("Drug Company"/"Pharmaceutical Company")
    pair — the canonical case for "preferredTerm and submissionValue
    diverge, both must validate"."""
    return FakeCT(
        codelists={
            "C_ORG_TYPE": [
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
        },
        klass_attribute_map={("Organization", "type"): "C_ORG_TYPE"},
    )


def _data_with(klass, instances):
    data = MagicMock()
    data.instances_by_klass.side_effect = lambda k: instances if k == klass else []
    data.path_by_id.return_value = "$.x"
    return data


def test_ct_check_accepts_preferred_term_decode():
    rt = RuleTemplate("R200", RuleTemplate.ERROR, "preferred ok")
    data = _data_with(
        "Organization",
        [{"id": "i1", "type": {"code": "C54149", "decode": "Drug Company"}}],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is True
    assert rt.errors().count() == 0


def test_ct_check_accepts_submission_value_decode():
    """C54149's submissionValue is 'Pharmaceutical Company' — must validate."""
    rt = RuleTemplate("R201", RuleTemplate.ERROR, "submission ok")
    data = _data_with(
        "Organization",
        [{"id": "i1", "type": {"code": "C54149", "decode": "Pharmaceutical Company"}}],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is True
    assert rt.errors().count() == 0


def test_ct_check_decode_match_is_case_insensitive():
    """After the predicate consolidation, decode matching uses casefold —
    'drug company' validates against preferredTerm 'Drug Company'.
    This is the drift fix versus the old _codes_and_decodes which used
    case-sensitive dict lookup. See the analysis in
    project_m11_sdtm_phase_code_tension."""
    rt = RuleTemplate("R202", RuleTemplate.ERROR, "case insensitive decode")
    data = _data_with(
        "Organization",
        [{"id": "i1", "type": {"code": "C54149", "decode": "drug company"}}],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is True
    assert rt.errors().count() == 0


def test_ct_check_concept_id_match_remains_case_sensitive():
    """NCI conceptIds are uppercase; lowercase 'c54149' must NOT match
    'C54149'. The casefold applies to PT and submissionValue only —
    by="concept_id" in find_in_codelist is case-sensitive."""
    rt = RuleTemplate("R203", RuleTemplate.ERROR, "concept_id case-sensitive")
    data = _data_with(
        "Organization",
        [{"id": "i1", "type": {"code": "c54149", "decode": "Drug Company"}}],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is False
    assert rt.errors().count() == 1


# ---------------------------------------------------------------------------
# _ct_check — failure paths
# ---------------------------------------------------------------------------


def test_ct_check_rejects_decode_that_is_neither_pt_nor_sv():
    rt = RuleTemplate("R300", RuleTemplate.ERROR, "neither label")
    data = _data_with(
        "Organization",
        [{"id": "i1", "type": {"code": "C54149", "decode": "Pharma"}}],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is False
    assert rt.errors().count() == 1


def test_ct_check_pair_mismatch_when_code_from_one_term_decode_from_another():
    """code=C54149 (term 0) paired with decode='Study Registry' (term 1)
    is a pair mismatch — both label and code are valid in the codelist,
    but they're from different terms. The conceptId-based check
    (find_in_codelist returns the full term) preserves this semantics."""
    rt = RuleTemplate("R301", RuleTemplate.ERROR, "pair mismatch")
    data = _data_with(
        "Organization",
        [{"id": "i1", "type": {"code": "C54149", "decode": "Study Registry"}}],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is False
    assert rt.errors().count() == 1
    entries = rt.errors().to_dict(level=0)
    assert any("do not match" in e["message"] for e in entries)


def test_ct_check_pair_mismatch_also_detected_when_decode_is_other_terms_submission_value():
    """Same as above but the decode is the other term's submissionValue
    (not preferredTerm). Still a mismatch — both labels resolve to
    different terms."""
    rt = RuleTemplate("R302", RuleTemplate.ERROR, "pair mismatch SV")
    data = _data_with(
        "Organization",
        [{"id": "i1", "type": {"code": "C54149", "decode": "Clinical Study Registry"}}],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is False
    assert rt.errors().count() == 1


def test_ct_check_invalid_code_only_is_error():
    rt = RuleTemplate("R303", RuleTemplate.ERROR, "code invalid")
    data = _data_with(
        "Organization",
        [{"id": "i1", "type": {"code": "BAD", "decode": "Drug Company"}}],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is False
    entries = rt.errors().to_dict(level=0)
    assert any("not in the codelist" in e["message"] for e in entries)


def test_ct_check_invalid_decode_only_is_error():
    rt = RuleTemplate("R304", RuleTemplate.ERROR, "decode invalid")
    data = _data_with(
        "Organization",
        [{"id": "i1", "type": {"code": "C54149", "decode": "BAD"}}],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is False
    entries = rt.errors().to_dict(level=0)
    assert any("not in the codelist" in e["message"] for e in entries)


def test_ct_check_neither_code_nor_decode_in_codelist_is_single_error():
    rt = RuleTemplate("R305", RuleTemplate.ERROR, "neither in codelist")
    data = _data_with(
        "Organization",
        [{"id": "i1", "type": {"code": "BAD", "decode": "BAD"}}],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is False
    assert rt.errors().count() == 1
    entries = rt.errors().to_dict(level=0)
    assert any("neither" in e["message"].lower() for e in entries)


def test_ct_check_missing_attribute_is_error():
    rt = RuleTemplate("R306", RuleTemplate.ERROR, "missing attribute")
    data = _data_with("Organization", [{"id": "i1"}])  # no 'type'
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is False
    entries = rt.errors().to_dict(level=0)
    assert any("Missing attribute" in e["message"] for e in entries)


# ---------------------------------------------------------------------------
# _ct_check — null / non-dict item handling
# ---------------------------------------------------------------------------


def test_ct_check_skips_null_item():
    """An optional Code attribute set to None is a legitimate empty value,
    not an invalid code."""
    rt = RuleTemplate("R400", RuleTemplate.ERROR, "null item")
    data = _data_with("Organization", [{"id": "i1", "type": None}])
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is True
    assert rt.errors().count() == 0


def test_ct_check_unwraps_alias_code_standard_code():
    """AliasCode-shaped attributes carry code/decode on standardCode.
    The unwrap is preserved across the refactor."""
    rt = RuleTemplate("R401", RuleTemplate.ERROR, "AliasCode unwrap")
    data = _data_with(
        "Organization",
        [
            {
                "id": "i1",
                "type": {
                    "id": "AliasCode_X",
                    "standardCode": {"code": "C54149", "decode": "Drug Company"},
                },
            }
        ],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is True
    assert rt.errors().count() == 0


def test_ct_check_handles_list_valued_attribute():
    """If the attribute is a list of Codes, each entry is checked."""
    rt = RuleTemplate("R402", RuleTemplate.ERROR, "list of codes")
    data = _data_with(
        "Organization",
        [
            {
                "id": "i1",
                "type": [
                    {"code": "C54149", "decode": "Drug Company"},  # valid
                    {"code": "BAD", "decode": "BAD"},  # invalid
                ],
            }
        ],
    )
    ok = rt._ct_check({"data": data, "ct": _ct_with_c54149()}, "Organization", "type")
    assert ok is False
    assert rt.errors().count() == 1
