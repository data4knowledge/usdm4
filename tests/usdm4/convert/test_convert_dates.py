"""Convert: every governance date type mapping on both the document version
and the study version — approval (C132352 -> C71476), effective
(C207598 -> C215663) and any other code left as it is."""

import copy
import json

from tests.usdm4.helpers.files import file_path
from usdm4.convert.convert import Convert

CODES = {"C132352": "C71476", "C207598": "C215663", "C99999": "C99999"}


def _dates(template: dict) -> list[dict]:
    result = []
    for index, code in enumerate(CODES, start=1):
        date = copy.deepcopy(template)
        date["id"] = f"{date['id']}_{index}"
        date["type"]["code"] = code
        result.append(date)
    return result


def _study():
    with open(file_path("convert", "example_1.json")) as f:
        data = json.load(f)
    study = data["study"]
    version = study["versions"][0]
    document_version = study["documentedBy"]["versions"][0]
    version["dateValues"] = _dates(version["dateValues"][0])
    document_version["dateValues"] = _dates(document_version["dateValues"][0])
    return data


def _codes(dates) -> list[str]:
    return [d.type.code for d in dates]


def test_document_version_date_types():
    result = Convert.convert(_study())
    document = result.study.documentedBy[0].versions[0]
    assert _codes(document.dateValues) == list(CODES.values())


def test_study_version_date_types():
    result = Convert.convert(_study())
    version = result.study.versions[0]
    assert _codes(version.dateValues) == list(CODES.values())
