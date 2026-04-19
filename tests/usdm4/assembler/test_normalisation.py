"""Unit tests for ``usdm4.assembler.normalisation``.

The module is small but its semantics matter: producers (the encoder)
call ``record_normalisation`` to publish coercion events that downstream
validators read. The helper has to suppress no-op normalisations (source
already canonical), tag entries with the agreed ``error_type``, and put
the structured payload in ``extra`` not the message.
"""

from unittest.mock import Mock

import pytest
from simple_error_log.errors import Errors

from usdm4.assembler.normalisation import (
    KIND_COERCED,
    KIND_UNMAPPED,
    M11_NORMALIZATION_RECORD,
    record_normalisation,
)


@pytest.fixture
def errors() -> Errors:
    return Errors()


# --- coerced records -----------------------------------------------------


class TestCoercedRecords:
    def test_emits_warning_when_source_differs_from_normalised(self, errors):
        record_normalisation(
            errors,
            element="Trial Phase",
            source="Phase III",
            normalised="Phase 3",
            kind=KIND_COERCED,
        )
        assert errors.count() == 1
        item = errors._items[0]
        assert item.error_type == M11_NORMALIZATION_RECORD
        assert item.extra == {
            "element": "Trial Phase",
            "source": "Phase III",
            "normalised": "Phase 3",
            "kind": KIND_COERCED,
        }
        # Warning so it surfaces in the default error dump.
        assert item.level == Errors.WARNING

    def test_suppresses_when_source_already_canonical(self, errors):
        # No coercion actually happened; recording one would be noise.
        record_normalisation(
            errors,
            element="Trial Phase",
            source="Phase 3",
            normalised="Phase 3",
            kind=KIND_COERCED,
        )
        assert errors.count() == 0

    def test_suppresses_when_only_whitespace_differs(self, errors):
        record_normalisation(
            errors,
            element="Trial Phase",
            source="  Phase 3  ",
            normalised="Phase 3",
            kind=KIND_COERCED,
        )
        assert errors.count() == 0

    def test_suppresses_when_only_case_differs(self, errors):
        record_normalisation(
            errors,
            element="Geographic Scope",
            source="GLOBAL",
            normalised="Global",
            kind=KIND_COERCED,
        )
        assert errors.count() == 0


# --- unmapped records ---------------------------------------------------


class TestUnmappedRecords:
    def test_emits_warning_with_unmapped_kind(self, errors):
        record_normalisation(
            errors,
            element="Trial Phase",
            source="Phase XIV",
            normalised="[Trial Phase] Not Applicable",
            kind=KIND_UNMAPPED,
        )
        assert errors.count() == 1
        item = errors._items[0]
        assert item.extra["kind"] == KIND_UNMAPPED
        assert item.extra["source"] == "Phase XIV"
        assert item.extra["normalised"] == "[Trial Phase] Not Applicable"

    def test_unmapped_emits_even_when_values_equal(self, errors):
        # Suppression only applies to coerced. Unmapped is a real signal
        # even when source happens to look like the default.
        record_normalisation(
            errors,
            element="Document Status",
            source="Draft",
            normalised="Draft",
            kind=KIND_UNMAPPED,
        )
        assert errors.count() == 1


# --- message + filterability --------------------------------------------


class TestRecordShape:
    def test_message_is_human_readable(self, errors):
        record_normalisation(
            errors,
            element="Trial Phase",
            source="Phase III",
            normalised="Phase 3",
        )
        msg = errors._items[0].message
        # Message content isn't load-bearing for consumers (they read
        # extra) but it's what surfaces in error dumps, so check it
        # mentions the salient pieces.
        assert "Trial Phase" in msg
        assert "Phase III" in msg
        assert "Phase 3" in msg

    def test_filter_by_error_type_finds_only_records(self, errors):
        # Mix in unrelated entries to verify the filter pattern works.
        errors.info("unrelated info")
        record_normalisation(
            errors, element="Trial Phase", source="II", normalised="Phase 2"
        )
        errors.warning("unrelated warning")
        record_normalisation(
            errors, element="Document Status", source="DFT", normalised="Draft"
        )

        records = [
            i for i in errors._items if i.error_type == M11_NORMALIZATION_RECORD
        ]
        assert len(records) == 2
        elements = [r.extra["element"] for r in records]
        assert elements == ["Trial Phase", "Document Status"]


# --- defaults & edge cases ---------------------------------------------


class TestDefaults:
    def test_default_kind_is_coerced(self, errors):
        record_normalisation(
            errors, element="Trial Phase", source="II", normalised="Phase 2"
        )
        assert errors._items[0].extra["kind"] == KIND_COERCED

    def test_handles_none_source(self, errors):
        # Encoder occasionally passes None when the docx field is absent;
        # don't crash.
        record_normalisation(
            errors,
            element="Trial Phase",
            source=None,
            normalised="Phase 3",
            kind=KIND_COERCED,
        )
        # None != "Phase 3" so an entry is emitted, not suppressed.
        assert errors.count() == 1

    def test_passes_location_through(self, errors):
        location = Mock()
        record_normalisation(
            errors,
            element="Trial Phase",
            source="II",
            normalised="Phase 2",
            location=location,
        )
        assert errors._items[0].location is location
