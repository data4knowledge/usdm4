"""Duplicate id fix (GitHub 106)."""

from usdm4.fixer.fix_result import FixResult
from usdm4.fixer.id_fixer import IdFixer


def code(iid, value="C1"):
    return {"id": iid, "code": value, "decode": "x", "instanceType": "Code"}


def run(data):
    result = FixResult(data)
    IdFixer(result).fix()
    return result


def test_no_duplicates_no_changes():
    data = {"id": "S", "instanceType": "Study", "a": code("C1")}
    result = run(data)
    assert result.changes == [] and result.issues == []


def test_same_class_unreferenced_renumbered():
    data = {
        "id": "S",
        "instanceType": "Study",
        "codes": [code("C1"), code("C1"), code("C1"), code("C1_3")],
    }
    result = run(data)
    ids = [c["id"] for c in data["codes"]]
    assert ids == ["C1", "C1_2", "C1_4", "C1_3"]
    assert [c.path for c in result.changes] == ["$.codes[1]", "$.codes[2]"]
    assert result.changes[0].reason == "duplicate id"
    assert result.issues == []


def test_same_class_referenced_is_an_error():
    data = {
        "id": "S",
        "instanceType": "Study",
        "orgs": [
            {"id": "O1", "instanceType": "Organization"},
            {"id": "O1", "instanceType": "Organization"},
        ],
        "ident": {"id": "I1", "instanceType": "StudyIdentifier", "scopeId": "O1"},
    }
    result = run(data)
    assert result.changes == []
    assert [i.path for i in result.issues] == ["$.orgs[0]", "$.orgs[1]"]
    assert "input error" in result.issues[0].message
    assert "$.ident.scopeId" in result.issues[0].message


def test_same_class_referenced_through_superclass_is_an_error():
    data = {
        "id": "S",
        "instanceType": "Study",
        "instances": [
            {"id": "D", "instanceType": "ScheduledDecisionInstance"},
            {"id": "D", "instanceType": "ScheduledDecisionInstance"},
        ],
        "timeline": {"id": "T", "instanceType": "ScheduleTimeline", "entryId": "D"},
    }
    result = run(data)
    assert result.changes == []
    assert len(result.issues) == 2


def test_cross_class_renumbered_and_references_follow():
    data = {
        "id": "S",
        "instanceType": "Study",
        "epoch": {"id": "X", "instanceType": "StudyEpoch"},
        "arm": {"id": "X", "instanceType": "StudyArm"},
        "cells": [
            {
                "id": "CELL",
                "instanceType": "StudyCell",
                "armId": "X",
                "epochId": "X",
                "elementIds": ["E"],
            }
        ],
        "element": {"id": "E", "instanceType": "StudyElement"},
    }
    result = run(data)
    assert data["epoch"]["id"] == "X"
    assert data["arm"]["id"] == "X_2"
    assert data["cells"][0]["armId"] == "X_2"
    assert data["cells"][0]["epochId"] == "X"
    assert [(c.path, c.old, c.new) for c in result.changes] == [
        ("$.arm", "X", "X_2"),
        ("$.cells[0].armId", "X", "X_2"),
    ]
    assert result.changes[0].reason == "id also used by StudyEpoch"


def test_cross_class_list_reference_follows():
    data = {
        "id": "S",
        "instanceType": "Study",
        "bc": {"id": "X", "instanceType": "BiomedicalConcept"},
        "act": {"id": "X", "instanceType": "Activity", "biomedicalConceptIds": ["X"]},
        "sai": {
            "id": "SAI",
            "instanceType": "ScheduledActivityInstance",
            "activityIds": ["A", "X"],
        },
    }
    result = run(data)
    assert data["act"]["id"] == "X_2"
    assert data["act"]["biomedicalConceptIds"] == ["X"]
    assert data["sai"]["activityIds"] == ["A", "X_2"]
    assert ("$.sai.activityIds[1]", "X_2") in [(c.path, c.new) for c in result.changes]


def test_cross_class_ambiguous_reference_left_alone():
    data = {
        "id": "S",
        "instanceType": "Study",
        "act": {"id": "X", "instanceType": "Activity"},
        "sai": {"id": "X", "instanceType": "ScheduledActivityInstance"},
        "cond": {"id": "C", "instanceType": "Condition", "contextIds": ["X"]},
    }
    result = run(data)
    assert result.changes == []
    assert data["sai"]["id"] == "X"
    assert len(result.issues) == 1
    assert "could point at Activity, ScheduledActivityInstance" in (
        result.issues[0].message
    )


def test_cross_class_non_keeper_same_class_groups():
    data = {
        "id": "S",
        "instanceType": "Study",
        "items": [
            {"id": "X", "instanceType": "StudyEpoch"},
            {"id": "X", "instanceType": "Organization"},
            {"id": "X", "instanceType": "Organization"},
            {"id": "X", "instanceType": "StudyArm"},
            {"id": "X", "instanceType": "StudyArm"},
        ],
        "ident": {"id": "I", "instanceType": "StudyIdentifier", "scopeId": "X"},
    }
    result = run(data)
    assert [i["id"] for i in data["items"]] == ["X", "X", "X", "X_2", "X_3"]
    assert len(result.issues) == 2
    assert data["ident"]["scopeId"] == "X"


def test_text_reference_follows_by_klass():
    text = (
        '<p>See <usdm:ref attribute="name" id="X" klass="StudyArm"/> and '
        '<usdm:ref klass="StudyEpoch" id="X" attribute="name"></usdm:ref> and '
        '<usdm:ref attribute="name" klass="StudyArm"/></p>'
    )
    data = {
        "id": "S",
        "instanceType": "Study",
        "epoch": {"id": "X", "instanceType": "StudyEpoch"},
        "arm": {"id": "X", "instanceType": "StudyArm"},
        "item": {"id": "N", "instanceType": "NarrativeContentItem", "text": text},
        "item2": {
            "id": "N2",
            "instanceType": "NarrativeContentItem",
            "text": '<usdm:ref attribute="name" id="X" klass="StudyEpoch"/>',
        },
    }
    result = run(data)
    assert data["arm"]["id"] == "X_2"
    assert 'id="X_2" klass="StudyArm"' in data["item"]["text"]
    assert 'klass="StudyEpoch" id="X"' in data["item"]["text"]
    assert data["item2"]["text"] == (
        '<usdm:ref attribute="name" id="X" klass="StudyEpoch"/>'
    )
    text_changes = [c for c in result.changes if c.attribute == "text"]
    assert len(text_changes) == 1
    assert text_changes[0].reason == "usdm:ref follows changed id"


def test_text_reference_without_klass_is_ambiguous():
    data = {
        "id": "S",
        "instanceType": "Study",
        "epoch": {"id": "X", "instanceType": "StudyEpoch"},
        "arm": {"id": "X", "instanceType": "StudyArm"},
        "item": {
            "id": "N",
            "instanceType": "NarrativeContentItem",
            "text": '<usdm:ref attribute="name" id="X"/>',
        },
    }
    result = run(data)
    assert result.changes == []
    assert result.issues[0].path == "$.item.text"


def test_text_reference_to_same_class_duplicate_is_an_error():
    data = {
        "id": "S",
        "instanceType": "Study",
        "arms": [
            {"id": "X", "instanceType": "StudyArm"},
            {"id": "X", "instanceType": "StudyArm"},
        ],
        "item": {
            "id": "N",
            "instanceType": "NarrativeContentItem",
            "text": '<usdm:ref attribute="name" id="X" klass="StudyArm"/>',
        },
    }
    result = run(data)
    assert result.changes == []
    assert len(result.issues) == 2


def test_text_with_no_duplicate_reference_untouched():
    data = {
        "id": "S",
        "instanceType": "Study",
        "epoch": {"id": "X", "instanceType": "StudyEpoch"},
        "arm": {"id": "X", "instanceType": "StudyArm"},
        "cell": {"id": "C", "instanceType": "StudyCell", "armId": "X"},
        "item": {
            "id": "N",
            "instanceType": "NarrativeContentItem",
            "text": '<usdm:ref attribute="name" id="Other" klass="StudyArm"/>',
        },
    }
    result = run(data)
    assert data["item"]["text"].count('id="Other"') == 1
    assert data["cell"]["armId"] == "X_2"
    assert all(c.attribute != "text" for c in result.changes)


def test_reference_to_unrelated_class_not_rewritten():
    data = {
        "id": "S",
        "instanceType": "Study",
        "epoch": {"id": "X", "instanceType": "StudyEpoch"},
        "arm": {"id": "X", "instanceType": "StudyArm"},
        "org": {"id": "X", "instanceType": "Organization"},
        "cell": {"id": "C", "instanceType": "StudyCell", "epochId": "X", "armId": 3},
        "role": {"id": "R", "instanceType": "StudyRole", "organizationIds": [1]},
    }
    result = run(data)
    assert data["cell"]["epochId"] == "X"
    assert [c.path for c in result.changes] == ["$.arm", "$.org"]


def test_unsafe_ids_made_uri_safe_and_references_follow():
    data = {
        "id": "S",
        "instanceType": "Study",
        "orgs": [
            {"id": "ADJUDICATION COMMITTEE", "instanceType": "Organization"},
            {"id": "10^12/L", "instanceType": "Organization"},
            {"id": "10_12_L", "instanceType": "Organization"},
            {"id": "^^", "instanceType": "Organization"},
            {"id": "Org-1.a", "instanceType": "Organization"},
        ],
        "role": {
            "id": "R",
            "instanceType": "StudyRole",
            "organizationIds": ["ADJUDICATION COMMITTEE", "10^12/L"],
        },
        "item": {
            "id": "N",
            "instanceType": "NarrativeContentItem",
            "text": '<usdm:ref attribute="name" id="10^12/L" klass="Organization"/>'
            '<usdm:ref attribute="name" id="ADJUDICATION COMMITTEE"/>',
        },
    }
    result = run(data)
    assert [o["id"] for o in data["orgs"]] == [
        "ADJUDICATION_COMMITTEE",
        "10_12_L_2",
        "10_12_L",
        "id",
        "Org-1.a",
    ]
    assert data["role"]["organizationIds"] == ["ADJUDICATION_COMMITTEE", "10_12_L_2"]
    assert 'id="10_12_L_2"' in data["item"]["text"]
    assert 'id="ADJUDICATION_COMMITTEE"' in data["item"]["text"]
    reasons = {c.reason for c in result.changes}
    assert reasons == {
        "id not URI-safe",
        "reference follows changed id",
        "usdm:ref follows changed id",
    }


def test_unsafe_duplicates_renumbered_then_made_safe():
    data = {
        "id": "S",
        "instanceType": "Study",
        "codes": [code("FEMORAL ARTERY"), code("FEMORAL ARTERY")],
    }
    run(data)
    assert [c["id"] for c in data["codes"]] == ["FEMORAL_ARTERY", "FEMORAL_ARTERY_2"]


def test_unsafe_referenced_duplicate_made_safe_and_still_reported():
    data = {
        "id": "S",
        "instanceType": "Study",
        "orgs": [
            {"id": "A B", "instanceType": "Organization"},
            {"id": "A B", "instanceType": "Organization"},
        ],
        "ident": {"id": "I", "instanceType": "StudyIdentifier", "scopeId": "A B"},
        "item": {
            "id": "N",
            "instanceType": "NarrativeContentItem",
            "text": '<usdm:ref attribute="name" id="A B"/>',
        },
    }
    result = run(data)
    assert [o["id"] for o in data["orgs"]] == ["A_B", "A_B"]
    assert data["ident"]["scopeId"] == "A_B"
    assert data["item"]["text"] == '<usdm:ref attribute="name" id="A_B"/>'
    assert len(result.issues) == 2
    assert [c.reason for c in result.changes].count("id not URI-safe") == 2
