"""Branch-coverage supplements for CoreCacheManager.

The main test suite covers the happy paths for caching and loading
resources.  These tests hit the remaining low-traffic branches:

- JSONDecodeError / OSError fallbacks in the three load_cached_* methods
- clear() when the directory exists
- _prepare_api_resources exception handlers (rules + CT index)
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from usdm4.core.core_cache_manager import CoreCacheManager


# ---------------------------------------------------------------------------
# JSONDecodeError / OSError fallbacks
# ---------------------------------------------------------------------------


@pytest.fixture
def manager(tmp_path):
    return CoreCacheManager(cache_dir=str(tmp_path / "cache"))


def test_load_cached_rules_returns_none_for_missing_file(manager):
    """Missing file path returns None without attempting a read."""
    assert manager.load_cached_rules("usdm", "4-0") is None


def test_load_cached_rules_returns_none_on_decode_error(manager):
    """Corrupt JSON in the cached rules file → JSONDecodeError caught,
    returning None (lines 457-458)."""
    rules_dir = manager.cache_dir / "rules" / "usdm"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / "4-0.json").write_text("not valid json")
    assert manager.load_cached_rules("usdm", "4-0") is None


def test_load_cached_ct_packages_returns_none_for_missing_file(manager):
    """Missing CT index file returns None."""
    assert manager.load_cached_ct_packages() is None


def test_load_cached_ct_packages_returns_none_on_decode_error(manager):
    """Corrupt JSON in the CT package index file → JSONDecodeError caught,
    returning None (lines 490-491)."""
    ct_dir = manager.cache_dir / "ct"
    ct_dir.mkdir(parents=True, exist_ok=True)
    (ct_dir / "published_packages.json").write_text("{not json")
    assert manager.load_cached_ct_packages() is None


def test_load_cached_ct_package_data_returns_none_for_missing_file(manager):
    """Missing CT package data file returns None."""
    assert manager.load_cached_ct_package_data("sdtmct-2024-01-01") is None


def test_load_cached_ct_package_data_returns_none_on_decode_error(manager):
    """Corrupt JSON in a CT package data file → JSONDecodeError caught,
    returning None (lines 526-527)."""
    data_dir = manager.cache_dir / "ct" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "sdtmct-2024-01-01.json").write_text("<<<corrupt>>>")
    assert manager.load_cached_ct_package_data("sdtmct-2024-01-01") is None


# ---------------------------------------------------------------------------
# Happy-path companions — confirm load_* reads cached data back
# ---------------------------------------------------------------------------


def test_cache_and_load_rules_round_trip(manager):
    rules = [{"core_id": "R1"}, {"core_id": "R2"}]
    manager.cache_rules("usdm", "4-0", rules)
    assert manager.load_cached_rules("usdm", "4-0") == rules


def test_cache_and_load_ct_packages_round_trip(manager):
    packages = ["sdtmct-2024-01-01", "cdashct-2024-01-01"]
    manager.cache_ct_packages(packages)
    assert manager.load_cached_ct_packages() == packages


def test_cache_and_load_ct_package_data_round_trip(manager):
    data = {"C123": "Concept"}
    manager.cache_ct_package_data("sdtmct-2024-01-01", data)
    assert manager.load_cached_ct_package_data("sdtmct-2024-01-01") == data


# ---------------------------------------------------------------------------
# clear() wipes and recreates the cache directory
# ---------------------------------------------------------------------------


def test_clear_removes_and_recreates_cache_dir(manager):
    """clear() rmtree's the cache dir then remakes it (lines 417-419)."""
    # Add a file so we can verify it disappears.
    (manager.cache_dir / "marker.txt").write_text("hello")
    assert (manager.cache_dir / "marker.txt").exists()

    manager.clear()

    assert manager.cache_dir.exists()
    assert not (manager.cache_dir / "marker.txt").exists()


# ---------------------------------------------------------------------------
# _prepare_api_resources exception handlers
# ---------------------------------------------------------------------------


def test_prepare_api_resources_logs_rules_download_failure(manager, caplog):
    """When CDISCLibraryService.get_rules_by_catalog raises, the except
    block logs a warning and execution continues to the CT-index branch
    (lines 339-340)."""
    fake_library = MagicMock()
    fake_library.get_rules_by_catalog.side_effect = RuntimeError("rules boom")
    fake_library.get_all_ct_packages.return_value = []

    fake_cache = MagicMock()

    with (
        patch("cdisc_rules_engine.services.cache.CacheServiceFactory") as factory_cls,
        patch(
            "cdisc_rules_engine.services.cdisc_library_service.CDISCLibraryService",
            return_value=fake_library,
        ),
    ):
        factory_cls.return_value.get_cache_service.return_value = fake_cache

        with caplog.at_level("WARNING"):
            manager._prepare_api_resources("4-0", "api-key-abc")

    assert any(
        "Failed to download rules" in record.message for record in caplog.records
    )


def test_prepare_api_resources_logs_ct_index_download_failure(manager, caplog):
    """When CDISCLibraryService.get_all_ct_packages raises, the except
    block logs a warning and the method returns cleanly (lines 353-354)."""
    fake_library = MagicMock()
    fake_library.get_rules_by_catalog.return_value = {"rules": [{"core_id": "R1"}]}
    fake_library.get_all_ct_packages.side_effect = RuntimeError("ct boom")

    fake_cache = MagicMock()

    with (
        patch("cdisc_rules_engine.services.cache.CacheServiceFactory") as factory_cls,
        patch(
            "cdisc_rules_engine.services.cdisc_library_service.CDISCLibraryService",
            return_value=fake_library,
        ),
    ):
        factory_cls.return_value.get_cache_service.return_value = fake_cache

        with caplog.at_level("WARNING"):
            manager._prepare_api_resources("4-0", "api-key-abc")

    assert any(
        "Failed to download CT package index" in record.message
        for record in caplog.records
    )


def test_prepare_api_resources_handles_rules_as_plain_list(manager):
    """When get_rules_by_catalog returns a list rather than a dict, the
    method still caches correctly (covers the `isinstance(result, dict)`
    else-branch in line 336)."""
    fake_library = MagicMock()
    fake_library.get_rules_by_catalog.return_value = [
        {"core_id": "R1"},
        {"core_id": "R2"},
    ]
    fake_library.get_all_ct_packages.return_value = [
        {"href": "/mdr/ct/packages/sdtmct-2024-01-01"}
    ]

    fake_cache = MagicMock()

    with (
        patch("cdisc_rules_engine.services.cache.CacheServiceFactory") as factory_cls,
        patch(
            "cdisc_rules_engine.services.cdisc_library_service.CDISCLibraryService",
            return_value=fake_library,
        ),
    ):
        factory_cls.return_value.get_cache_service.return_value = fake_cache
        manager._prepare_api_resources("4-0", "api-key-abc")

    # Rules + CT index both persisted
    assert manager.load_cached_rules("usdm", "4-0") == [
        {"core_id": "R1"},
        {"core_id": "R2"},
    ]
    assert manager.load_cached_ct_packages() == ["sdtmct-2024-01-01"]


# ---------------------------------------------------------------------------
# prepare() top-level branches
# ---------------------------------------------------------------------------


def test_prepare_returns_early_when_already_populated(manager):
    """If is_populated reports ready, prepare() short-circuits (line 288)."""
    # Fake a fully-populated state so is_populated() returns ready=True
    # without touching the network.
    with patch.object(manager, "is_populated") as ip:
        from usdm4.core.core_cache_manager import CacheStatus

        ip.return_value = CacheStatus(
            ready=True,
            has_resources=True,
            has_rules=True,
            has_ct_index=True,
            cache_dir=str(manager.cache_dir),
            details=[],
        )
        status = manager.prepare()
    assert status.ready


def test_prepare_warns_when_api_key_missing(manager, caplog, monkeypatch):
    """If rules/CT are missing but no API key is available, prepare() logs
    a warning and does not call _prepare_api_resources (lines 303-308)."""
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)

    # Short-circuit GitHub downloads to no-ops.
    with (
        patch.object(manager, "_ensure_jsonata_resources") as jsonata,
        patch.object(manager, "_ensure_xsd_schema_resources") as xsd,
        patch.object(manager, "_prepare_api_resources") as api_prep,
    ):
        with caplog.at_level("WARNING"):
            manager.prepare(api_key=None)
        jsonata.assert_called_once()
        xsd.assert_called_once()
        api_prep.assert_not_called()

    assert any("API key not available" in record.message for record in caplog.records)


# ---------------------------------------------------------------------------
# cache_ct_package_data replaces "/" with "_" in filenames
# ---------------------------------------------------------------------------


def test_cache_ct_package_data_sanitises_slash_in_name(manager):
    """Package names containing "/" are translated to "_" to produce a
    safe filename."""
    manager.cache_ct_package_data("group/package", {"k": "v"})
    # Loading by the same name should round-trip.
    assert manager.load_cached_ct_package_data("group/package") == {"k": "v"}
    # And the on-disk file should not contain a "/" in its stem.
    ct_data_dir = manager.cache_dir / "ct" / "data"
    files = list(ct_data_dir.iterdir())
    assert len(files) == 1
    assert files[0].name == "group_package.json"


# ---------------------------------------------------------------------------
# Legibility sanity: cache_rules writes valid JSON
# ---------------------------------------------------------------------------


def test_cache_rules_produces_valid_json_on_disk(manager):
    manager.cache_rules("usdm", "4-0", [{"core_id": "R1"}])
    rules_file = manager.cache_dir / "rules" / "usdm" / "4-0.json"
    assert rules_file.exists()
    # Parses independently.
    parsed = json.loads(rules_file.read_text())
    assert parsed == [{"core_id": "R1"}]
