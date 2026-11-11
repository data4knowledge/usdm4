"""Timepoint._code_dict: a note's code as a plain dict."""

from usdm4.api.code import Code
from usdm4.expander.timepoint import Timepoint


def test_code_dict():
    code = Code(
        id="c1",
        code="C25473",
        codeSystem="http://www.cdisc.org",
        codeSystemVersion="2024-03-29",
        decode="Daily",
        instanceType="Code",
    )
    timepoint = Timepoint.__new__(Timepoint)
    assert timepoint._code_dict(code) == {
        "code": "C25473",
        "decode": "Daily",
        "system": "http://www.cdisc.org",
        "version": "2024-03-29",
    }
