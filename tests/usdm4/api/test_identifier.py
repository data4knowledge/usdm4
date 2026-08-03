"""Tests for StudyIdentifier helpers: scoped_by, of_type, is_sponsor."""

from src.usdm4.api.identifier import StudyIdentifier
from src.usdm4.api.organization import Organization
from src.usdm4.api.code import Code
from src.usdm4.api.extension import ExtensionAttribute, BaseCode
from src.usdm4.api.extensions_d4k import SIT_EXT_URL


def _make_code(code: str, decode: str = "decode") -> Code:
    return Code(
        id="C1",
        code=code,
        codeSystem="CDISC",
        codeSystemVersion="1",
        decode=decode,
        instanceType="Code",
    )


def _make_base_code(code: str, decode: str = "decode") -> BaseCode:
    """BaseCode is the shape ExtensionAttribute.valueCode expects."""
    return BaseCode(
        id="BC1",
        code=code,
        codeSystem="CDISC",
        codeSystemVersion="1",
        decode=decode,
        instanceType="Code",
    )


def _make_org(org_type_code: str) -> Organization:
    return Organization(
        id="ORG1",
        name="TestOrg",
        identifier="I1",
        identifierScheme="TEST",
        label="Test",
        type=_make_code(org_type_code, "OrgType"),
        legalAddress=None,
        instanceType="Organization",
    )


def _make_study_identifier() -> StudyIdentifier:
    return StudyIdentifier(
        id="SID1",
        text="STUDY-001",
        scopeId="ORG1",
        instanceType="StudyIdentifier",
    )


def test_scoped_by_returns_organization():
    """Covers StudyIdentifier.scoped_by."""
    org = _make_org("C54149")
    sid = _make_study_identifier()
    org_map = {"ORG1": org}
    assert sid.scoped_by(org_map) is org


def test_is_sponsor_true_for_drug_company_code():
    sid = _make_study_identifier()
    org = _make_org("C54149")
    assert sid.is_sponsor({"ORG1": org}) is True


def test_is_sponsor_false_for_other_code():
    sid = _make_study_identifier()
    org = _make_org("C93453")
    assert sid.is_sponsor({"ORG1": org}) is False


def test_of_type_returns_none_when_no_extension():
    sid = _make_study_identifier()
    assert sid.of_type() is None


def test_of_type_returns_extension_value_code():
    sid = _make_study_identifier()
    code = _make_base_code("X", "X-decode")
    ext = ExtensionAttribute(
        id="E1",
        url=SIT_EXT_URL,
        valueCode=code,
        instanceType="ExtensionAttribute",
    )
    sid.extensionAttributes = [ext]
    result = sid.of_type()
    # Pydantic may rebuild the model on assignment, so compare by value
    assert result is not None
    assert result.code == "X"
    assert result.decode == "X-decode"
