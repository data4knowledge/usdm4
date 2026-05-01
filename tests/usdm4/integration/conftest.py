"""Shared fixtures for assembler-driven integration tests.

These tests cover the full pipeline:

    AssemblerInput dict
        -> Assembler.execute
        -> Wrapper.model_dump
        -> JSON file
        -> validate (d4k) / validate_core (CDISC CORE)

The fixtures here build a *minimal valid* AssemblerInput. It is not meant to
exercise every assembler feature; it is the smallest payload that:

  * passes ``AssemblerInput.model_validate``,
  * runs ``Assembler.execute`` end-to-end without errors,
  * produces a Wrapper that serialises to JSON,
  * is conformant enough that d4k reports zero failing rules.

If you find yourself adding fields to make a new test pass, prefer extending
the dict in a test-local helper rather than bloating the fixture — the value
of this fixture is that it stays small and obviously correct.

Note on imports: tests under ``tests/usdm4/`` use the ``usdm4.*`` import path
(NOT ``src.usdm4.*``). The two paths register as distinct class objects and
break ``isinstance`` checks downstream.
"""

from __future__ import annotations

import json
import os
import pathlib
import tempfile

import pytest
from simple_error_log.errors import Errors

from usdm4 import USDM4
from usdm4.assembler.assembler import Assembler


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _root_path() -> str:
    """Repository-relative path to ``src/usdm4`` (matches conftest.py)."""
    base = pathlib.Path(__file__).resolve().parents[3]
    return os.path.join(base, "src/usdm4")


# ---------------------------------------------------------------------------
# Input fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def minimum_assembler_input() -> dict:
    """The smallest AssemblerInput we expect to round-trip cleanly.

    Mirrors the existing unit-test fixture in
    ``tests/usdm4/assembler/test_assembler.py`` but with a single SOA timeline
    so we exercise the timeline branch as well.
    """
    return {
        "identification": {
            "titles": {
                "brief": "Integration Test Study",
                "official": "Integration Test Study — Official",
            },
            "identifiers": [
                {"identifier": "NCT99999999", "scope": {"standard": "nct"}}
            ],
        },
        "document": {
            "document": {
                "label": "Integration Test Protocol",
                "version": "1.0",
                "status": "final",
                "template": "Test Template",
                "version_date": "2026-01-01",
            },
            "sections": [
                {
                    "section_number": "1",
                    "section_title": "Introduction",
                    "text": "Hello, world.",
                }
            ],
        },
        "population": {
            "label": "Integration Test Population",
            "inclusion_exclusion": {
                "inclusion": ["Age >= 18 years"],
                "exclusion": ["Pregnant"],
            },
        },
        "amendments": {
            "summary": "Initial version",
            "reasons": {"primary": "First version"},
            "impact": {"safety": False, "reliability": False},
            "enrollment": {"value": 100, "unit": "subjects"},
        },
        "study_design": {
            "label": "Integration Test Study Design",
            "rationale": "Test rationale",
            "trial_phase": "phase-1",
        },
        "study": {
            "name": {"acronym": "ITST"},
            "label": "Integration Test Study",
            "version": "1.0",
            "rationale": "Integration test",
        },
        "soa": {
            "epochs": {
                "items": [
                    {"text": "Screening"},
                    {"text": "Treatment"},
                ]
            },
            "visits": {
                "items": [
                    {"text": "Visit 1", "references": []},
                    {"text": "Visit 2", "references": []},
                ]
            },
            "timepoints": {
                "items": [
                    {"index": "0", "text": "Day 1", "value": "1", "unit": "days"},
                    {"index": "1", "text": "Day 7", "value": "7", "unit": "days"},
                ]
            },
            "windows": {
                "items": [
                    {"before": 0, "after": 0, "unit": "days"},
                    {"before": 1, "after": 1, "unit": "days"},
                ]
            },
            "activities": {
                "items": [
                    {
                        "name": "Consent",
                        "visits": [{"index": 0, "references": []}],
                    },
                    {
                        "name": "Blood Draw",
                        "visits": [{"index": 1, "references": []}],
                    },
                ]
            },
            "conditions": {"items": []},
        },
    }


# ---------------------------------------------------------------------------
# Assembled-study fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def assembled_study_json_path(
    minimum_assembler_input: dict, tmp_path: pathlib.Path
) -> pathlib.Path:
    """Run the assembler over the minimum input and write Wrapper JSON to disk.

    Fails the test outright if the assembler can't build a study from the
    minimum fixture — that is itself a regression we want surfaced.
    """
    errors = Errors()
    assembler = Assembler(_root_path(), errors)
    assembler.execute(minimum_assembler_input)

    assert assembler.study is not None, (
        f"Assembler produced no Study from the minimum fixture. "
        f"Errors:\n{errors.dump(level=Errors.ERROR)}"
    )

    wrapper = assembler.wrapper(
        name="usdm4-integration-tests", version="0.0.1"
    )
    assert wrapper is not None, (
        f"Assembler.wrapper returned None. "
        f"Errors:\n{errors.dump(level=Errors.ERROR)}"
    )

    out_path = tmp_path / "assembled_minimum.json"
    with out_path.open("w") as fh:
        json.dump(wrapper.model_dump(by_alias=True), fh, default=str)
    return out_path


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


@pytest.fixture
def usdm4_facade() -> USDM4:
    """A USDM4 facade with default cache settings."""
    return USDM4()
