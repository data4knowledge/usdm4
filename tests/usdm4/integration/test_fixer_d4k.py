"""Integration: USDM4().fix() on sample 7 with injected faults, then d4k
(GitHub 106).

Sample 7 is clean of the faults the fixer handles. The test breaks a copy of
it in the ways real extraction output is broken, fixes it, and validates the
result with d4k:

  * three Codes share one id (same class, not referenced),
  * an Encounter takes a StudyEpoch's id, with every reference to the
    Encounter following it (different classes, both referenced, so one is
    renumbered and its references rewritten),
  * a CDISC Code has a codeSystemVersion that is not a release date,
  * a StudyEpoch type has a decode that is neither the preferred term nor
    the submission value.

The fixed file must fail exactly the rules the untouched sample fails, with
no rule raising, so any fix that breaks a reference or a code shows up as a
new failing rule.
"""

from __future__ import annotations

import copy
import json
import pathlib

import pytest

from usdm4 import USDM4
from usdm4.fixer.walk import instances
from usdm4.rules.results import RuleStatus

SAMPLE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "test_files/integration/sample_usdm_7.json"
)
CLASH = "StudyEpoch_1"
ENCOUNTER = "Encounter_1"


def failing(result) -> frozenset:
    return frozenset(
        rid for rid, o in result.outcomes.items() if o.status == RuleStatus.FAILURE
    )


def raising(result) -> list:
    return [
        rid for rid, o in result.outcomes.items() if o.status == RuleStatus.EXCEPTION
    ]


def break_sample(data: dict) -> dict:
    data = copy.deepcopy(data)
    found = instances(data)
    codes = [i.node for i in found if i.klass == "Code"]
    for code in codes[1:3]:
        code["id"] = codes[0]["id"]
    for instance in found:
        node = instance.node
        if node["id"] == ENCOUNTER:
            node["id"] = CLASH
        for key in ("encounterId", "nextId", "previousId"):
            if node.get(key) == ENCOUNTER and instance.klass in (
                "Encounter",
                "ScheduledActivityInstance",
            ):
                node[key] = CLASH
    cdisc = [c for c in codes if c.get("codeSystem") == "http://www.cdisc.org"]
    cdisc[-1]["codeSystemVersion"] = "26.10d"
    design = data["study"]["versions"][0]["studyDesigns"][0]
    design["epochs"][0]["type"]["decode"] = "Wrong decode"
    return data


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    if not SAMPLE_PATH.exists():
        pytest.skip(f"Sample file not found: {SAMPLE_PATH}")
    folder = tmp_path_factory.mktemp("fixer")
    broken_path = folder / "broken.json"
    fixed_path = folder / "fixed.json"
    broken = break_sample(json.loads(SAMPLE_PATH.read_text()))
    broken_path.write_text(json.dumps(broken))
    usdm = USDM4()
    result = usdm.fix(str(broken_path))
    result.save(str(fixed_path))
    return {
        "result": result,
        "clean": usdm.validate(str(SAMPLE_PATH)),
        "broken": usdm.validate(str(broken_path)),
        "fixed": usdm.validate(str(fixed_path)),
    }


def test_faults_are_seen_before_the_fix(run):
    assert {"DDF00083", "DDF00155"} <= failing(run["broken"])


def test_fixed_file_fails_only_what_the_sample_fails(run):
    assert raising(run["fixed"]) == []
    assert failing(run["fixed"]) == failing(run["clean"])


def test_references_follow_the_renumbered_object(run):
    """Whichever class comes first in the file keeps the id. The other is
    renumbered, and each reference ends up on its own class."""
    found = instances(run["result"].data)
    ids = {
        i.klass: i.node["id"]
        for i in found
        if i.klass in ("Encounter", "StudyEpoch") and i.node["id"].startswith(CLASH)
    }
    assert sorted(ids.values()) == [CLASH, f"{CLASH}_2"]
    sais = [i.node for i in found if i.klass == "ScheduledActivityInstance"]
    cells = [i.node for i in found if i.klass == "StudyCell"]
    assert any(s.get("encounterId") == ids["Encounter"] for s in sais)
    assert any(c.get("epochId") == ids["StudyEpoch"] for c in cells)
    renamed = next(k for k, v in ids.items() if v == f"{CLASH}_2")
    keeper = ids["Encounter" if renamed == "StudyEpoch" else "StudyEpoch"]
    attribute = "epochId" if renamed == "StudyEpoch" else "encounterId"
    assert all(s.get(attribute) != keeper for s in sais)


def test_every_change_logged_and_nothing_left(run):
    result = run["result"]
    assert result.issues == []
    steps = {(c.step, c.attribute) for c in result.changes}
    assert {
        ("ids", "id"),
        ("ct", "codeSystemVersion"),
        ("ct", "decode"),
    } <= steps
