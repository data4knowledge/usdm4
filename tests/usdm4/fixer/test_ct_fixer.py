"""CT version and decode fix (GitHub 106)."""

import json

import pytest

from usdm4 import USDM4
from usdm4.ct.cdisc.library import MissingCodelistError
from usdm4.fixer.ct_fixer import CTFixer
from usdm4.fixer.fix_result import FixResult
from usdm4.fixer.fixer import Fixer

CODELIST = {
    "conceptId": "C188724",
    "source": {"effective_date": "2026-03-27", "package": "ddfct"},
    "terms": [
        {
            "conceptId": "C93453",
            "preferredTerm": "Study Registry",
            "submissionValue": "Registry",
        },
        {
            "conceptId": "C999",
            "preferredTerm": "Extra",
            "submissionValue": "EXTRA",
            "source": "m11",
        },
    ],
}


class StubLibrary:
    def klass_and_attribute(self, klass, attribute):
        if (klass, attribute) in (("Organization", "type"), ("StudyDesign", "ta")):
            return CODELIST
        if attribute == "broken":
            raise MissingCodelistError("Codelist 'C1' is not loaded")
        return None

    def effective_dates(self):
        return {"2026-03-27"}


def code(value, decode, version="2024-09-27", system="http://www.cdisc.org"):
    return {
        "id": f"Code_{value}",
        "code": value,
        "codeSystem": system,
        "codeSystemVersion": version,
        "decode": decode,
        "instanceType": "Code",
    }


def org(type_value):
    return {"id": "O", "instanceType": "Organization", "name": "x", "type": type_value}


def run(data):
    result = FixResult(data)
    CTFixer(result, StubLibrary()).fix()
    return result


def test_valid_version_kept_decode_set():
    data = org(code("C93453", "Registry thing"))
    result = run(data)
    assert data["type"]["codeSystemVersion"] == "2024-09-27"
    assert data["type"]["decode"] == "Study Registry"
    assert [(c.path, c.old, c.new) for c in result.changes] == [
        ("$.type.decode", "Registry thing", "Study Registry"),
    ]
    assert result.issues == []


def test_invalid_versions_get_most_used_valid_date():
    data = {
        "id": "S",
        "instanceType": "Study",
        "a": code("C1", "x", version="2024-09-27"),
        "b": code("C2", "x", version="2024-09-27"),
        "c": code("C3", "x", version="2026-03-27"),
        "d": code("C4", "x", version="26.10d"),
        "e": {**code("C5", "x"), "codeSystemVersion": None},
        "f": code("C6", "x", version="bad", system="NCIT"),
    }
    result = run(data)
    assert [(c.path, c.old, c.new) for c in result.changes] == [
        ("$.d.codeSystemVersion", "26.10d", "2024-09-27"),
        ("$.e.codeSystemVersion", None, "2024-09-27"),
    ]
    assert result.changes[0].reason == (
        "not a CDISC release date; release date most used in file"
    )
    assert data["c"]["codeSystemVersion"] == "2026-03-27"
    assert data["f"]["codeSystemVersion"] == "bad"


def test_no_valid_version_uses_cache_date():
    data = org(code("C93453", "Study Registry", version="2019"))
    result = run(data)
    assert data["type"]["codeSystemVersion"] == "2026-03-27"
    assert result.changes[0].reason == "not a CDISC release date; CT cache date"


def test_submission_value_decode_kept():
    data = org(code("C93453", "Registry", version="2026-03-27"))
    result = run(data)
    assert data["type"]["decode"] == "Registry"
    assert result.changes == []


def test_code_not_in_codelist_reported_not_changed():
    data = org(code("C17998", "Unknown"))
    result = run(data)
    assert data["type"]["codeSystemVersion"] == "2024-09-27"
    assert result.changes == []
    assert "not in codelist C188724" in result.issues[0].message


def test_wrong_code_system_reported_not_changed():
    data = org(code("C93453", "Study Registry", system="cdisc.org"))
    result = run(data)
    assert data["type"]["codeSystem"] == "cdisc.org"
    assert result.changes == []
    assert "codeSystem 'cdisc.org'" in result.issues[0].message


def test_extension_term_code_system_not_reported():
    data = org(code("C999", "Extra", system="other"))
    result = run(data)
    assert result.issues == []


def test_alias_code_and_list_and_superclass():
    alias = {
        "id": "A",
        "instanceType": "AliasCode",
        "standardCode": code("C93453", "x"),
        "standardCodeAliases": [],
    }
    data = {
        "id": "SD",
        "instanceType": "InterventionalStudyDesign",
        "ta": [alias, "junk", {"id": "Q", "instanceType": "Quantity"}],
    }
    result = run(data)
    assert alias["standardCode"]["decode"] == "Study Registry"
    assert result.changes[0].path == "$.ta[0].standardCode.decode"


def test_alias_code_without_standard_code_skipped():
    data = {
        "id": "SD",
        "instanceType": "InterventionalStudyDesign",
        "ta": {"id": "A", "instanceType": "AliasCode", "standardCode": None},
    }
    assert run(data).changes == []


def test_unmapped_and_missing_codelist():
    data = {
        "id": "X",
        "instanceType": "Activity",
        "other": code("C93453", "x"),
        "broken": code("C93453", "x"),
    }
    result = run(data)
    assert result.changes == []
    assert result.issues[0].path == "$.broken"


def test_fixer_runs_steps_and_keeps_input():
    data = {
        "id": "S",
        "instanceType": "Study",
        "orgs": [org(code("C93453", "x")), org(code("C93453", "x"))],
    }
    result = Fixer(StubLibrary()).fix(data)
    assert data["orgs"][1]["id"] == "O"
    assert result.data["orgs"][1]["id"] == "O_2"
    assert result.summary() == {"changes": {"ids": 2, "ct": 2}, "issues": {}}
    data["orgs"][0]["type"]["code"] = "C17998"
    assert Fixer(StubLibrary()).fix(data).summary()["issues"] == {"ct": 1}
    assert Fixer().fix(data, ct=False).summary()["changes"] == {"ids": 2}
    with pytest.raises(ValueError):
        Fixer().fix(data)


def test_facade_with_real_library(tmp_path):
    source = tmp_path / "in.json"
    data = {
        "id": "S",
        "instanceType": "Study",
        "orgs": [org(code("C93453", "x")), org(code("C93453", "x"))],
    }
    source.write_text(json.dumps(data))
    result = USDM4().fix(str(source))
    assert result.data["orgs"][1]["id"] == "O_2"
    assert result.data["orgs"][0]["type"]["decode"] == "Study Registry"
    out, log = tmp_path / "out.json", tmp_path / "log.json"
    result.save(str(out))
    result.save_log(str(log))
    assert json.loads(out.read_text()) == result.data
    saved = json.loads(log.read_text())
    assert saved["summary"]["changes"]["ids"] == 2
    assert saved["changes"][0]["step"] == "ids"
    assert json.loads(source.read_text()) == data
    assert USDM4().fix(str(source), ct=False).summary()["changes"] == {"ids": 2}
