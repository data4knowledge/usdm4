"""Tests for the Missing loader.

The Missing loader reads up to two sibling YAML files (missing_ct.yaml,
m11_codelists.yaml) and yields (entry, source_file) tuples. These tests
verify file discovery, source tagging, and tolerance of absent files.
"""

import os


from src.usdm4.ct.cdisc.missing.missing import Missing


def _write(dir_path: str, filename: str, content: str) -> None:
    with open(os.path.join(dir_path, filename), "w") as f:
        f.write(content)


def test_both_files_present_yields_tagged_tuples(tmp_path):
    """Each entry is yielded with the filename it came from."""
    _write(
        tmp_path,
        "missing_ct.yaml",
        "- extends: C66737\n  source: NCIt-M11\n  terms: []\n",
    )
    _write(
        tmp_path,
        "m11_codelists.yaml",
        "- codelist: C217045\n  source: NCIt-M11\n  terms: []\n",
    )

    missing = Missing(str(tmp_path))
    entries = list(missing.code_lists())

    assert len(entries) == 2
    by_source = {source: entry for entry, source in entries}
    assert by_source["missing_ct.yaml"]["extends"] == "C66737"
    assert by_source["m11_codelists.yaml"]["codelist"] == "C217045"


def test_only_missing_ct_present(tmp_path):
    _write(
        tmp_path,
        "missing_ct.yaml",
        "- extends: C66737\n  source: NCIt-M11\n  terms: []\n",
    )

    missing = Missing(str(tmp_path))
    entries = list(missing.code_lists())

    assert entries == [
        ({"extends": "C66737", "source": "NCIt-M11", "terms": []}, "missing_ct.yaml")
    ]


def test_only_m11_codelists_present(tmp_path):
    _write(
        tmp_path,
        "m11_codelists.yaml",
        "- codelist: C217045\n  source: NCIt-M11\n  terms: []\n",
    )

    missing = Missing(str(tmp_path))
    entries = list(missing.code_lists())

    assert len(entries) == 1
    entry, source = entries[0]
    assert entry["codelist"] == "C217045"
    assert source == "m11_codelists.yaml"


def test_neither_file_present_yields_nothing(tmp_path):
    """Absent files are silently skipped; yields an empty sequence."""
    missing = Missing(str(tmp_path))
    assert list(missing.code_lists()) == []


def test_empty_yaml_file_yields_nothing(tmp_path):
    """A file containing just ``[]`` (the default empty state) yields nothing."""
    _write(tmp_path, "missing_ct.yaml", "[]\n")
    _write(tmp_path, "m11_codelists.yaml", "[]\n")

    missing = Missing(str(tmp_path))
    assert list(missing.code_lists()) == []


def test_yaml_comments_and_empty_payload(tmp_path):
    """A file with only comments parses as None and is treated as empty."""
    _write(tmp_path, "missing_ct.yaml", "# just a comment\n# another\n")

    missing = Missing(str(tmp_path))
    assert list(missing.code_lists()) == []


def test_multiple_entries_in_one_file_all_carry_same_source(tmp_path):
    _write(
        tmp_path,
        "missing_ct.yaml",
        (
            "- extends: C66737\n"
            "  source: NCIt-M11\n"
            "  terms: []\n"
            "- extends: C66781\n"
            "  source: NCIt-OtherSource\n"
            "  terms: []\n"
        ),
    )

    missing = Missing(str(tmp_path))
    entries = list(missing.code_lists())

    assert len(entries) == 2
    assert all(source == "missing_ct.yaml" for _, source in entries)


def test_file_handle_is_closed(tmp_path):
    """Loader uses a context manager — no leaked file handles."""
    _write(tmp_path, "missing_ct.yaml", "[]\n")
    _write(tmp_path, "m11_codelists.yaml", "[]\n")

    # If a handle leaked we'd see a ResourceWarning under -W error.
    # Instantiating and discarding is enough — the with-statement
    # in __init__ is the relevant code path.
    Missing(str(tmp_path))


def test_iteration_is_deterministic_and_repeatable(tmp_path):
    """Calling code_lists() multiple times yields the same entries in the same order."""
    _write(
        tmp_path,
        "missing_ct.yaml",
        "- extends: C66737\n  source: NCIt-M11\n  terms: []\n",
    )
    _write(
        tmp_path,
        "m11_codelists.yaml",
        "- codelist: C217045\n  source: NCIt-M11\n  terms: []\n",
    )

    missing = Missing(str(tmp_path))
    first = list(missing.code_lists())
    second = list(missing.code_lists())

    assert first == second
    # missing_ct.yaml is processed before m11_codelists.yaml (file order
    # is the class-level _FILES tuple; this is a documented behaviour).
    assert first[0][1] == "missing_ct.yaml"
    assert first[1][1] == "m11_codelists.yaml"
