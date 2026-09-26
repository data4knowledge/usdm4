"""Pin of the timeline assembler's output — issue 63, parts 63.1 and 63.5.

63.1 recorded what ``TimelineAssembler`` built BEFORE the restructure, from
inputs in the old ``TimelineInput`` shape. 63.5 rewrote those inputs once,
mechanically, into ``ScheduleTimelineInput``; the restructured assembler
reproduces the 63.1 output exactly, apart from the differences listed in
``docs/timeline_assembler_plan.md`` 63.5, each recorded with its reason.

Inputs live in ``tests/usdm4/test_files/timeline_pin/input_*.json`` (a
``source`` note, a ``converted`` note, and the ``soa`` list). Expected output
is written next to them as ``expected_*.json``.

To (re)create the pin: set ``SAVE = True``, run this file once, set it back
to ``False``, run again. Only ever re-save on purpose — a re-save is a
statement that the new output is the right output.
"""

import json
import os
import pathlib

import pytest
from simple_error_log.errors import Errors

from src.usdm4.api.serialize import serialize_as_json
from src.usdm4.assembler.schema.schedule_timeline_schema import (
    ScheduleTimelineInput,
)
from src.usdm4.assembler.timeline_assembler import TimelineAssembler
from src.usdm4.builder.builder import Builder
from tests.usdm4.helpers.files import read_json_file, write_json_file

SAVE = False

SUB_DIR = "timeline_pin"
CASES = [
    "minimal",
    "features",
    "nct05565742",
    "nct06454630",
    "nct04557384",
    "nct05197426",
    "nct05565742_r6",
    "nct02674152_r7",
]


def root_path():
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    return Builder(root_path(), Errors())


def _input(case: str) -> list[dict]:
    """The input as the Assembler hands it on: validated against
    ``ScheduleTimelineInput`` and dumped, exactly as in production."""
    data = json.loads(read_json_file(SUB_DIR, f"input_{case}.json"))
    return [ScheduleTimelineInput.model_validate(t).model_dump() for t in data["soa"]]


def _output(assembler: TimelineAssembler) -> str:
    """Everything the other assemblers read from the timeline assembler."""
    return json.dumps(
        {
            "timelines": assembler.timelines,
            "epochs": assembler.epochs,
            "encounters": assembler.encounters,
            "activities": assembler.activities,
            "conditions": assembler.conditions,
            "biomedical_concepts": assembler.biomedical_concepts,
            "biomedical_concept_surrogates": assembler.biomedical_concept_surrogates,
        },
        default=serialize_as_json,
    )


@pytest.mark.parametrize("case", CASES)
def test_timeline_pin(builder, case):
    builder.clear()
    assembler = TimelineAssembler(builder, Errors())
    assembler.execute(_input(case))
    actual = _output(assembler)
    if SAVE:
        write_json_file(SUB_DIR, f"expected_{case}.json", actual)
    expected = read_json_file(SUB_DIR, f"expected_{case}.json")
    assert json.loads(actual) == json.loads(expected)


def test_pin_is_deterministic(builder):
    """The pin is only worth having if the same input gives the same output
    twice — ids come from the builder's counter, reset by ``clear``."""
    outputs = []
    for _ in range(2):
        builder.clear()
        assembler = TimelineAssembler(builder, Errors())
        assembler.execute(_input("features"))
        outputs.append(_output(assembler))
    assert outputs[0] == outputs[1]
