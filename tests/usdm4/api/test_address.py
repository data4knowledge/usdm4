from src.usdm4.api.address import Address
from src.usdm4.api.code import Code


def test_set_text():
    code = Code(
        id="dummy",
        code="code",
        codeSystem="cs",
        codeSystemVersion="csv",
        decode="decode",
        instanceType="Code",
    )
    address = Address(
        id="dummy",
        lines=["Line 1", "Line 2"],
        city="City",
        district="District",
        state="State",
        postalCode="12345",
        country=code,
        instanceType="Address",
    )
    address.set_text()
    assert address.text == "Line 1, Line 2, City, District, State, 12345, decode"
