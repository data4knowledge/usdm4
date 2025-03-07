import json
from usdm4.minimum.minimum import Minimum


def test_init():
    instance = Minimum.minimum("Test Study", "SPONSOR-1234", "1.0.0")
    instance.study.id = "FAKE-UUID"  # UUID is dynamic
    assert json.loads(instance.to_json()) == {
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
                        "id": "Code_6",
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
                                                "id": "Code_7",
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
                                        "id": "Code_8",
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
                                "id": "Code_5",
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
                                        "id": "Code_7",
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
                                "id": "Code_8",
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
                                "id": "Code_4",
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
        "systemVersion": "0.1.0",
        "usdmVersion": "3.6.0",
    }
