import json
from src.usdm4 import USDM4

# from tests.rules.helpers import clear_rules_library
from src.usdm4.__version__ import __package_version__


def test_validate(tmp_path):
    # Create temporary test file
    # clear_rules_library() Not needed yet
    test_file = tmp_path / "validate.json"
    with open(test_file, "w") as f:
        json.dump(_expected(), f)
    result = USDM4().validate(test_file)
    assert result.passed_or_not_implemented()


def test_example_1():
    test_file = "tests/test_files/package/example_1.json"
    result = USDM4().validate(test_file)
    assert not result.passed_or_not_implemented()


def test_example_2():
    test_file = "tests/test_files/package/example_2.json"
    result = USDM4().validate(test_file)
    # print(f"RESULT: {[k for k, v in result._items.items() if v['status'] not in ['Not Implemented', 'Success']]}")
    assert result.passed_or_not_implemented()


def test_validate_error(tmp_path):
    # Create temporary test file
    # clear_rules_library() Not needed yet
    test_file = tmp_path / "validate.json"
    with open(test_file, "w") as f:
        json.dump(_bad(), f)
    result = USDM4().validate(test_file)
    assert not result.passed_or_not_implemented()


def test_minimum():
    result = USDM4().minimum("Test Study", "SPONSOR-1234", "1")
    result.study.id = "FAKE-UUID"
    model_dump = result.model_dump()
    model_dump["study"]["documentedBy"][0]["versions"][0]["dateValues"][0][
        "dateValue"
    ] = "2006-06-01"
    model_dump["study"]["versions"][0]["dateValues"][0]["dateValue"] = "2006-06-01"
    assert model_dump == _expected()


def _bad():
    data = _expected()
    # print(f"DATA: {type(data)}")
    data["study"]["documentedBy"][0]["id"] = None
    return data


def _expected():
    return {
        "study": {
            "description": "Test Study",
            "documentedBy": [
                {
                    "description": "The entire protocol document",
                    "id": "StudyDefinitionDocument_1",
                    "instanceType": "StudyDefinitionDocument",
                    "label": "Protocol Document",
                    "language": {
                        "code": "en",
                        "codeSystem": "ISO 639-1",
                        "codeSystemVersion": "2007",
                        "decode": "English",
                        "id": "Code_1",
                        "instanceType": "Code",
                    },
                    "name": "PROTOCOL DOCUMENT",
                    "notes": [],
                    "templateName": "Sponsor",
                    "type": {
                        "code": "C70817",
                        "codeSystem": "cdisc.org",
                        "codeSystemVersion": "2023-12-15",
                        "decode": "Protocol",
                        "id": "Code_5",
                        "instanceType": "Code",
                    },
                    "versions": [
                        {
                            "childIds": [],
                            "contents": [],
                            "dateValues": [
                                {
                                    "dateValue": "2006-06-01",
                                    "description": "Design approval date",
                                    "geographicScopes": [
                                        {
                                            "code": None,
                                            "id": "GeographicScope_1",
                                            "instanceType": "GeographicScope",
                                            "type": {
                                                "code": "C68846",
                                                "codeSystem": "cdisc.org",
                                                "codeSystemVersion": "2023-12-15",
                                                "decode": "Global",
                                                "id": "Code_6",
                                                "instanceType": "Code",
                                            },
                                        },
                                    ],
                                    "id": "GovernanceDate_1",
                                    "instanceType": "GovernanceDate",
                                    "label": "Design Approval",
                                    "name": "D_APPROVE",
                                    "type": {
                                        "code": "C132352",
                                        "codeSystem": "cdisc.org",
                                        "codeSystemVersion": "2023-12-15",
                                        "decode": "Sponsor Approval Date",
                                        "id": "Code_7",
                                        "instanceType": "Code",
                                    },
                                },
                            ],
                            "id": "StudyDefinitionDocumentVersion_1",
                            "instanceType": "StudyDefinitionDocumentVersion",
                            "notes": [],
                            "status": {
                                "code": "C25425",
                                "codeSystem": "cdisc.org",
                                "codeSystemVersion": "2023-12-15",
                                "decode": "Approved",
                                "id": "Code_4",
                                "instanceType": "Code",
                            },
                            "version": "1",
                        },
                    ],
                },
            ],
            "id": "FAKE-UUID",
            "instanceType": "Study",
            "label": "Test Study",
            "name": "Study",
            "versions": [
                {
                    "abbreviations": [],
                    "administrableProducts": [],
                    "amendments": [],
                    "businessTherapeuticAreas": [],
                    "criteria": [],
                    "dateValues": [
                        {
                            "dateValue": "2006-06-01",
                            "description": "Design approval date",
                            "geographicScopes": [
                                {
                                    "code": None,
                                    "id": "GeographicScope_1",
                                    "instanceType": "GeographicScope",
                                    "type": {
                                        "code": "C68846",
                                        "codeSystem": "cdisc.org",
                                        "codeSystemVersion": "2023-12-15",
                                        "decode": "Global",
                                        "id": "Code_6",
                                        "instanceType": "Code",
                                    },
                                },
                            ],
                            "id": "GovernanceDate_1",
                            "instanceType": "GovernanceDate",
                            "label": "Design Approval",
                            "name": "D_APPROVE",
                            "type": {
                                "code": "C132352",
                                "codeSystem": "cdisc.org",
                                "codeSystemVersion": "2023-12-15",
                                "decode": "Sponsor Approval Date",
                                "id": "Code_7",
                                "instanceType": "Code",
                            },
                        },
                    ],
                    "documentVersionIds": [],
                    "id": "StudyVersion_1",
                    "instanceType": "StudyVersion",
                    "narrativeContentItems": [],
                    "notes": [],
                    "organizations": [
                        {
                            "id": "Organization_1",
                            "identifier": "To be provided",
                            "identifierScheme": "To be provided",
                            "instanceType": "Organization",
                            "label": None,
                            "legalAddress": None,
                            "managedSites": [],
                            "name": "Sponsor",
                            "type": {
                                "code": "C70793",
                                "codeSystem": "cdisc.org",
                                "codeSystemVersion": "2023-12-15",
                                "decode": "Clinical Study Sponsor",
                                "id": "Code_3",
                                "instanceType": "Code",
                            },
                        },
                    ],
                    "rationale": "To be provided",
                    "referenceIdentifiers": [],
                    "roles": [],
                    "studyDesigns": [],
                    "studyIdentifiers": [
                        {
                            "id": "StudyIdentifier_1",
                            "instanceType": "StudyIdentifier",
                            "scopeId": "Organization_1",
                            "text": "SPONSOR-1234",
                        },
                    ],
                    "studyPhase": None,
                    "studyType": None,
                    "titles": [
                        {
                            "id": "StudyTitle_1",
                            "instanceType": "StudyTitle",
                            "text": "Test Study",
                            "type": {
                                "code": "C207616",
                                "codeSystem": "cdisc.org",
                                "codeSystemVersion": "2023-12-15",
                                "decode": "Official Study Title",
                                "id": "Code_2",
                                "instanceType": "Code",
                            },
                        },
                    ],
                    "versionIdentifier": "1",
                },
            ],
        },
        "systemName": "Python USDM4 Package",
        "systemVersion": __package_version__,
        "usdmVersion": "3.6.0",
    }
