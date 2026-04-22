"""Branch-coverage supplements for CoreValidator.

The primary test suite focuses on the validation pipeline via mocks.
These tests cover the file-validation error branches and the real
_import_engine entry point — both low-traffic paths that don't appear
in the primary suite.
"""

import json

import pytest


# ---------------------------------------------------------------------------
# _validate_file — error branches
# ---------------------------------------------------------------------------


@pytest.fixture
def validator(tmp_path):
    from usdm4.core.core_validator import CoreValidator

    return CoreValidator(cache_dir=str(tmp_path / "cache"), api_key="test-key-123")


def test_validate_file_raises_for_missing_file(validator, tmp_path):
    """FileNotFoundError surfaces when the path does not exist."""
    missing = tmp_path / "nope.json"
    with pytest.raises(FileNotFoundError):
        validator._validate_file(str(missing))


def test_validate_file_raises_for_wrong_extension(validator, tmp_path):
    """A non-.json path is rejected before JSON parsing is attempted."""
    f = tmp_path / "study.txt"
    f.write_text("{}")
    with pytest.raises(ValueError, match="Expected a JSON file"):
        validator._validate_file(str(f))


def test_validate_file_raises_for_missing_study_key(validator, tmp_path):
    """Valid JSON but no 'study' top-level key → ValueError."""
    f = tmp_path / "not_usdm.json"
    f.write_text(json.dumps({"other": "data"}))
    with pytest.raises(ValueError, match="missing 'study' key"):
        validator._validate_file(str(f))


def test_validate_file_accepts_valid_usdm(validator, tmp_path):
    """Happy path — a well-formed USDM JSON validates silently."""
    f = tmp_path / "study.json"
    f.write_text(json.dumps({"study": {"name": "S"}}))
    # Returns None, doesn't raise.
    assert validator._validate_file(str(f)) is None


# ---------------------------------------------------------------------------
# _load_ct_data — api-key-missing short circuit on uncached package
# ---------------------------------------------------------------------------


def test_load_ct_data_skips_uncached_without_api_key(tmp_path, monkeypatch):
    """When a package is uncached AND no API key is set, the per-version
    loop should `continue` without constructing a library_service (the
    `if not self._api_key: continue` branch — lines 435-436).
    """
    from unittest.mock import MagicMock

    from usdm4.core.core_validator import CoreValidator

    # CoreValidator.__init__ falls back to the env var if api_key is None,
    # and earlier tests in this module may have set it. Clear it so we
    # actually exercise the no-api-key branch.
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)

    v = CoreValidator(cache_dir=str(tmp_path / "cache"), api_key=None)
    # With no api_key, the cache_manager's load_cached_ct_package_data
    # returns None (nothing cached), and the per-version loop should skip
    # without invoking CDISCLibraryService.
    cache = MagicMock()
    FakeLibraryService = MagicMock()

    # Ensure the disk cache returns None so we hit the download branch.
    v._cache_manager.load_cached_ct_package_data = MagicMock(return_value=None)

    meta, loaded = v._load_ct_data(
        cache, FakeLibraryService, ["sdtmct-2023-09-29"], {"2023-09-29"}
    )

    assert meta == {}
    assert loaded == []
    # Library service never constructed because api_key is absent.
    FakeLibraryService.assert_not_called()


def test_load_ct_data_caches_downloaded_payload(tmp_path):
    """When the download returns data, it is both added to the returned
    metadata and persisted via cache_ct_package_data (lines 442-445)."""
    from unittest.mock import MagicMock

    from usdm4.core.core_validator import CoreValidator

    v = CoreValidator(cache_dir=str(tmp_path / "cache"), api_key="k")
    cache = MagicMock()
    v._cache_manager.load_cached_ct_package_data = MagicMock(return_value=None)
    v._cache_manager.cache_ct_package_data = MagicMock()

    fake_library = MagicMock()
    fake_library.get_codelist_terms_map.return_value = {"C123": "Concept"}
    FakeLibraryService = MagicMock(return_value=fake_library)

    meta, loaded = v._load_ct_data(
        cache, FakeLibraryService, ["sdtmct-2024-01-01"], {"2024-01-01"}
    )

    assert meta == {"sdtmct-2024-01-01": {"C123": "Concept"}}
    assert loaded == ["sdtmct-2024-01-01"]
    v._cache_manager.cache_ct_package_data.assert_called_once_with(
        "sdtmct-2024-01-01", {"C123": "Concept"}
    )


def test_load_ct_data_handles_download_exception(tmp_path):
    """If get_codelist_terms_map raises, the loop swallows the exception
    and continues (lines 446-447)."""
    from unittest.mock import MagicMock

    from usdm4.core.core_validator import CoreValidator

    v = CoreValidator(cache_dir=str(tmp_path / "cache"), api_key="k")
    cache = MagicMock()
    v._cache_manager.load_cached_ct_package_data = MagicMock(return_value=None)

    fake_library = MagicMock()
    fake_library.get_codelist_terms_map.side_effect = RuntimeError("network")
    FakeLibraryService = MagicMock(return_value=fake_library)

    meta, loaded = v._load_ct_data(
        cache, FakeLibraryService, ["sdtmct-2024-01-01"], {"2024-01-01"}
    )

    # Nothing accumulated; exception silently caught.
    assert meta == {}
    assert loaded == []


# ---------------------------------------------------------------------------
# _import_engine — deferred CDISC engine imports
# ---------------------------------------------------------------------------


def test_import_engine_returns_expected_bundle(tmp_path):
    """Calling _import_engine returns the mapping the pipeline expects.
    Covers the deferred-imports block (lines 175-197) which is otherwise
    only exercised in the full-validate path."""
    from pathlib import Path

    from usdm4.core.core_validator import CoreValidator

    v = CoreValidator(cache_dir=str(tmp_path / "cache"), api_key="k")
    bundle = v._import_engine()

    # All keys the pipeline consumes must be present.
    for key in (
        "package_dir",
        "config",
        "CacheServiceFactory",
        "RulesEngine",
        "get_rules_cache_key",
        "CDISCLibraryService",
        "PUBLISHED_CT_PACKAGES",
        "LibraryMetadataContainer",
    ):
        assert key in bundle

    # package_dir is resolved from the installed cdisc_rules_engine package.
    assert isinstance(bundle["package_dir"], Path)


# ---------------------------------------------------------------------------
# _extract_ct_versions — recursive dict/list traversal
# ---------------------------------------------------------------------------


def test_extract_ct_versions_deeply_nested():
    """Walk recurses into lists and dicts alike."""
    from usdm4.core.core_validator import CoreValidator

    data = {
        "study": {
            "codeSystemVersion": "2023",
            "nested": [
                {"codeSystemVersion": "2024"},
                [{"codeSystemVersion": "2025"}],
                "string-ignored",
            ],
        }
    }
    versions = CoreValidator._extract_ct_versions(data)
    assert versions == {"2023", "2024", "2025"}
