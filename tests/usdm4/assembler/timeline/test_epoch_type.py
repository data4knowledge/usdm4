"""Epoch type from the C99079 match — GitHub 93.

The heading's match in ``data/house_names.yaml`` already names the epoch
(``Screening`` -> ``SCR``); the same match now types it (``SCREENING`` ->
C202487 Screening Epoch). Unmatched and redacted epochs keep Treatment Epoch,
the type every epoch had before; an unmatched heading is warned. Names are
unchanged.
"""

import pytest
from simple_error_log.errors import Errors

from src.usdm4.assembler.timeline.naming import Naming
from src.usdm4.assembler.timeline_assembler import TimelineAssembler
from src.usdm4.builder.builder import Builder
from tests.usdm4.assembler.timeline.helpers import (
    activity,
    column,
    root_path,
    timeline,
)


@pytest.fixture(scope="module")
def builder():
    return Builder(root_path(), Errors())


def _epochs(builder, epochs: list[str]):
    builder.clear()
    errors = Errors()
    columns = [
        column(f"c{i}", epoch=e, visit=f"V{i}", timing=f"Day {i + 1}")
        for i, e in enumerate(epochs)
    ]
    soa = [timeline(columns, [activity("Vital signs", [c["id"] for c in columns])])]
    assembler = TimelineAssembler(builder, errors)
    assembler.execute(soa)
    return assembler.epochs, errors


def _warnings(errors: Errors) -> list[str]:
    return [e["message"] for e in errors.to_dict(level=Errors.WARNING)]


class TestEpochTerm:
    @pytest.mark.parametrize(
        "label, term",
        [
            ("Screening", "SCREENING"),
            ("Period I - Screening", "SCREENING"),
            ("Treatment Period", "TREATMENT"),
            ("Wash-out", "WASHOUT"),
            ("Follow-Up", "FOLLOW-UP"),
            ("Long-term follow-up", "LONG-TERM FOLLOW-UP"),
            ("Days 3-28", None),
            ("", None),
        ],
    )
    def test_match(self, label, term):
        assert Naming().epoch_term(label) == term

    @pytest.mark.parametrize(
        "label, name",
        [
            ("Screening", "SCR"),
            ("Follow-Up", "FU"),
            ("Long-term follow-up", "LTFU"),
            ("Bone marrow aspirate", "BMA"),
        ],
    )
    def test_names_unchanged(self, label, name):
        assert Naming().epoch_name(label, 1) == name

    def test_empty_label_named_by_index(self):
        assert Naming().epoch_name("", 3) == "EP3"


class TestEpochType:
    def test_typed_from_the_match(self, builder):
        epochs, _ = _epochs(
            builder, ["Screening", "Treatment", "Wash-out", "Follow-up"]
        )
        assert [(e.type.code, e.type.decode) for e in epochs] == [
            ("C202487", "Screening Epoch"),
            ("C101526", "Treatment Epoch"),
            ("C42872", "Washout Period"),
            ("C202578", "Follow-Up Epoch"),
        ]

    def test_names_as_before(self, builder):
        epochs, _ = _epochs(builder, ["Screening", "Treatment", "Follow-up"])
        assert [e.name for e in epochs] == ["SCR", "TREAT", "FU"]

    def test_unmatched_keeps_treatment_and_warns(self, builder):
        epochs, errors = _epochs(builder, ["Screening", "Days 3-28"])
        assert epochs[1].type.code == "C101526"
        assert any("'Days 3-28' matches no C99079 term" in w for w in _warnings(errors))

    def test_matched_does_not_warn(self, builder):
        _, errors = _epochs(builder, ["Screening", "Follow-up"])
        assert not any("C99079" in w for w in _warnings(errors))

    def test_redacted_keeps_treatment_without_warning(self, builder):
        epochs, errors = _epochs(builder, ["Screening", "CCI"])
        assert epochs[1].type.code == "C101526"
        assert not any("C99079" in w for w in _warnings(errors))
