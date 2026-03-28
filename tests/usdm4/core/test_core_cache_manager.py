"""Tests for CoreCacheManager, CacheStatus, and default_cache_dir."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from usdm4.core.core_cache_manager import (
    CacheStatus,
    CoreCacheManager,
    default_cache_dir,
)


@pytest.fixture
def cache_dir(tmp_path):
    """Provide a temporary cache directory."""
    return str(tmp_path / "test_cache")


@pytest.fixture
def manager(cache_dir):
    """Provide a CoreCacheManager with a temp directory."""
    return CoreCacheManager(cache_dir)


# ------------------------------------------------------------------
# default_cache_dir
# ------------------------------------------------------------------

class TestDefaultCacheDir:
    def test_returns_path(self):
        result = default_cache_dir()
        assert isinstance(result, Path)

    def test_ends_with_core(self):
        result = default_cache_dir()
        assert result.name == "core"
        assert result.parent.name == "usdm4"

    def test_uses_platformdirs(self):
        """Verify we delegate to platformdirs.user_cache_dir."""
        with patch("usdm4.core.core_cache_manager.user_cache_dir", return_value="/fake/cache/usdm4"):
            result = default_cache_dir()
        assert result == Path("/fake/cache/usdm4") / "core"


# ------------------------------------------------------------------
# CacheStatus
# ------------------------------------------------------------------

class TestCacheStatus:
    def test_default_values(self):
        status = CacheStatus()
        assert status.ready is False
        assert status.has_resources is False
        assert status.has_rules is False
        assert status.has_ct_index is False
        assert status.cache_dir == ""
        assert status.details == []

    def test_ready_when_all_true(self):
        status = CacheStatus(
            ready=True,
            has_resources=True,
            has_rules=True,
            has_ct_index=True,
            cache_dir="/some/dir",
        )
        assert status.ready is True
        assert status.details == []


# ------------------------------------------------------------------
# CoreCacheManager basics
# ------------------------------------------------------------------

class TestCoreCacheManager:
    def test_creates_cache_dir(self, cache_dir):
        mgr = CoreCacheManager(cache_dir)
        assert Path(cache_dir).exists()

    def test_default_cache_dir_uses_platformdirs(self):
        with patch("usdm4.core.core_cache_manager.user_cache_dir", return_value="/fake/cache/usdm4"):
            mgr = CoreCacheManager()
            assert mgr.cache_dir == Path("/fake/cache/usdm4") / "core"

    def test_custom_cache_dir(self, cache_dir):
        mgr = CoreCacheManager(cache_dir)
        assert mgr.cache_dir == Path(cache_dir)

    def test_resources_dir(self, manager):
        assert manager.resources_dir == manager.cache_dir / "resources"

    def test_jsonata_dir(self, manager):
        assert manager.jsonata_dir == manager.resources_dir / "jsonata"

    def test_schema_dir(self, manager):
        assert manager.schema_dir == manager.resources_dir / "schema" / "xml"

    def test_cache_and_load_rules(self, manager):
        rules = [
            {"core_id": "CORE-001", "description": "Test rule 1"},
            {"core_id": "CORE-002", "description": "Test rule 2"},
        ]
        manager.cache_rules("usdm", "4-0", rules)

        loaded = manager.load_cached_rules("usdm", "4-0")
        assert loaded is not None
        assert len(loaded) == 2
        assert loaded[0]["core_id"] == "CORE-001"

    def test_load_uncached_rules_returns_none(self, manager):
        assert manager.load_cached_rules("usdm", "4-0") is None

    def test_cache_and_load_ct_packages(self, manager):
        packages = ["sdtmct-2025-09-26", "ddfct-2025-09-26"]
        manager.cache_ct_packages(packages)

        loaded = manager.load_cached_ct_packages()
        assert loaded is not None
        assert len(loaded) == 2
        assert "sdtmct-2025-09-26" in loaded

    def test_load_uncached_ct_packages_returns_none(self, manager):
        assert manager.load_cached_ct_packages() is None

    def test_cache_and_load_ct_package_data(self, manager):
        data = {"C12345": {"code": "M", "decode": "Male"}}
        manager.cache_ct_package_data("sdtmct-2025-09-26", data)

        loaded = manager.load_cached_ct_package_data("sdtmct-2025-09-26")
        assert loaded is not None
        assert "C12345" in loaded

    def test_load_uncached_ct_package_data_returns_none(self, manager):
        assert manager.load_cached_ct_package_data("nonexistent") is None

    def test_clear(self, manager):
        # Create some cached data
        manager.cache_rules("usdm", "4-0", [{"core_id": "CORE-001"}])
        assert manager.load_cached_rules("usdm", "4-0") is not None

        # Clear
        manager.clear()

        # Should be gone
        assert manager.load_cached_rules("usdm", "4-0") is None
        # But the cache dir itself should still exist
        assert manager.cache_dir.exists()


# ------------------------------------------------------------------
# is_populated
# ------------------------------------------------------------------

class TestIsPopulated:
    def test_empty_cache_returns_not_ready(self, manager):
        status = manager.is_populated()
        assert status.ready is False
        assert status.has_resources is False
        assert status.has_rules is False
        assert status.has_ct_index is False
        assert len(status.details) > 0

    def test_cache_dir_in_status(self, manager, cache_dir):
        status = manager.is_populated()
        assert status.cache_dir == cache_dir

    def test_partial_population_resources_only(self, manager):
        """Populate JSONata and XSD but not rules or CT."""
        # Create jsonata files
        jsonata_dir = manager.jsonata_dir
        jsonata_dir.mkdir(parents=True, exist_ok=True)
        (jsonata_dir / "parse_refs.jsonata").write_text("// jsonata")

        # Create XSD sentinel
        xsd_dir = manager.schema_dir / "cdisc-usdm-xhtml-1.0"
        xsd_dir.mkdir(parents=True, exist_ok=True)
        (xsd_dir / "usdm-xhtml-1.0.xsd").write_text("<schema/>")

        status = manager.is_populated()
        assert status.has_resources is True
        assert status.has_rules is False
        assert status.has_ct_index is False
        assert status.ready is False

    def test_fully_populated(self, manager):
        """Simulate a fully populated cache."""
        # JSONata
        jsonata_dir = manager.jsonata_dir
        jsonata_dir.mkdir(parents=True, exist_ok=True)
        (jsonata_dir / "parse_refs.jsonata").write_text("// jsonata")

        # XSD sentinel
        xsd_dir = manager.schema_dir / "cdisc-usdm-xhtml-1.0"
        xsd_dir.mkdir(parents=True, exist_ok=True)
        (xsd_dir / "usdm-xhtml-1.0.xsd").write_text("<schema/>")

        # Rules
        manager.cache_rules("usdm", "4-0", [{"core_id": "CORE-001"}])

        # CT index
        manager.cache_ct_packages(["sdtmct-2025-09-26"])

        status = manager.is_populated("4-0")
        assert status.ready is True
        assert status.has_resources is True
        assert status.has_rules is True
        assert status.has_ct_index is True
        assert status.details == []

    def test_version_specific_rules(self, manager):
        """Rules cached for 4-0 should not satisfy a check for 3-0."""
        manager.cache_rules("usdm", "4-0", [{"core_id": "CORE-001"}])
        assert manager._has_rules("4-0") is True
        assert manager._has_rules("3-0") is False


# ------------------------------------------------------------------
# prepare (mocked — no network)
# ------------------------------------------------------------------

class TestPrepare:
    def test_returns_immediately_when_populated(self, manager):
        """If already populated, prepare() should not download anything."""
        # Populate everything
        jsonata_dir = manager.jsonata_dir
        jsonata_dir.mkdir(parents=True, exist_ok=True)
        (jsonata_dir / "parse_refs.jsonata").write_text("// jsonata")

        xsd_dir = manager.schema_dir / "cdisc-usdm-xhtml-1.0"
        xsd_dir.mkdir(parents=True, exist_ok=True)
        (xsd_dir / "usdm-xhtml-1.0.xsd").write_text("<schema/>")

        manager.cache_rules("usdm", "4-0", [{"core_id": "CORE-001"}])
        manager.cache_ct_packages(["sdtmct-2025-09-26"])

        # Patch ensure methods to ensure they are NOT called
        with patch.object(manager, "_ensure_jsonata_resources") as mock_jsonata, \
             patch.object(manager, "_ensure_xsd_schema_resources") as mock_xsd:
            status = manager.prepare("4-0", api_key="fake-key")

        mock_jsonata.assert_not_called()
        mock_xsd.assert_not_called()
        assert status.ready is True

    def test_downloads_resources_when_missing(self, manager):
        """If resources are missing, prepare() should attempt download."""
        # No resources at all — but also no API key, so only GitHub downloads attempted
        with patch.object(manager, "_ensure_jsonata_resources") as mock_jsonata, \
             patch.object(manager, "_ensure_xsd_schema_resources") as mock_xsd:
            manager.prepare("4-0")

        mock_jsonata.assert_called_once()
        mock_xsd.assert_called_once()

    def test_warns_without_api_key(self, manager, caplog):
        """Without an API key, prepare() should log a warning about rules/CT."""
        import logging

        # Populate resources to skip GitHub downloads
        jsonata_dir = manager.jsonata_dir
        jsonata_dir.mkdir(parents=True, exist_ok=True)
        (jsonata_dir / "sift_tree.jsonata").write_text("// jsonata")

        xsd_dir = manager.schema_dir / "cdisc-usdm-xhtml-1.0"
        xsd_dir.mkdir(parents=True, exist_ok=True)
        (xsd_dir / "usdm-xhtml-1.0.xsd").write_text("<schema/>")

        # Remove any env var
        env = {k: v for k, v in os.environ.items()
               if k not in ("CDISC_LIBRARY_API_KEY", "CDISC_API_KEY")}

        with patch.dict(os.environ, env, clear=True), \
             caplog.at_level(logging.WARNING, logger="usdm4.core.core_cache_manager"):
            manager.prepare("4-0")

        assert any("API key" in msg for msg in caplog.messages)


class TestCoreValidationResult:
    """Tests for CoreValidationResult data class."""

    def test_empty_result_is_valid(self):
        from usdm4.core.core_validation_result import CoreValidationResult

        result = CoreValidationResult()
        assert result.is_valid is True
        assert result.finding_count == 0

    def test_result_with_findings_is_not_valid(self):
        from usdm4.core.core_validation_result import (
            CoreRuleFinding,
            CoreValidationResult,
        )

        result = CoreValidationResult(
            findings=[
                CoreRuleFinding(
                    rule_id="CORE-001",
                    description="Test",
                    message="Something wrong",
                    errors=[{"value": "bad"}],
                )
            ]
        )
        assert result.is_valid is False
        assert result.finding_count == 1

    def test_format_text_passed(self):
        from usdm4.core.core_validation_result import CoreValidationResult

        result = CoreValidationResult(
            file_path="/test/study.json",
            version="4-0",
            rules_executed=100,
        )
        text = result.format_text()
        assert "Validation PASSED" in text
        assert "study.json" in text

    def test_format_text_with_findings(self):
        from usdm4.core.core_validation_result import (
            CoreRuleFinding,
            CoreValidationResult,
        )

        result = CoreValidationResult(
            file_path="/test/study.json",
            findings=[
                CoreRuleFinding(
                    rule_id="CORE-001",
                    description="Test rule",
                    message="Error message",
                    errors=[{"value": "bad"}, {"value": "also bad"}],
                )
            ],
            rules_executed=50,
        )
        text = result.format_text()
        assert "2 validation issue(s)" in text
        assert "CORE-001" in text

    def test_to_dict(self):
        from usdm4.core.core_validation_result import CoreValidationResult

        result = CoreValidationResult(
            file_path="/test/study.json",
            version="4-0",
            rules_executed=10,
        )
        d = result.to_dict()
        assert d["file"] == "/test/study.json"
        assert d["is_valid"] is True
        assert d["rules_executed"] == 10

    def test_to_errors_empty(self):
        from usdm4.core.core_validation_result import CoreValidationResult

        result = CoreValidationResult()
        errors = result.to_errors()
        assert errors.count() == 0

    def test_to_errors_with_findings(self):
        from usdm4.core.core_validation_result import (
            CoreRuleFinding,
            CoreValidationResult,
        )

        result = CoreValidationResult(
            findings=[
                CoreRuleFinding(
                    rule_id="CORE-001",
                    description="Test rule",
                    message="Something wrong",
                    errors=[{"value": "bad"}, {"value": "also bad"}],
                ),
                CoreRuleFinding(
                    rule_id="CORE-002",
                    description="Another rule",
                    message="",
                    errors=[{"value": "issue"}],
                ),
            ]
        )
        errors = result.to_errors()
        assert errors.count() == 3
        assert errors.error_count() == 3
        items = errors.to_dict()
        assert items[0]["type"] == "CORE-001"
        assert "Something wrong" in items[0]["message"]
        assert items[2]["type"] == "CORE-002"
        assert "Another rule" in items[2]["message"]


class TestCoreValidatorClassifyErrors:
    """Tests for the static _classify_errors method."""

    def test_empty_results(self):
        from usdm4.core.core_validator import CoreValidator

        real, exec_ = CoreValidator._classify_errors(None)
        assert real == []
        assert exec_ == []

    def test_separates_real_from_execution_errors(self):
        from usdm4.core.core_validator import CoreValidator

        results = {
            "dataset1": {
                "errors": [
                    {"value": "bad_data", "dataset": "X"},
                    {"error": "Column not found in data", "dataset": "Y"},
                    {"error": "Error occurred during dataset preprocessing", "dataset": "Z"},
                ]
            }
        }
        real, exec_ = CoreValidator._classify_errors(results)
        assert len(real) == 1
        assert real[0]["value"] == "bad_data"
        assert len(exec_) == 2

    def test_handles_list_values(self):
        from usdm4.core.core_validator import CoreValidator

        results = {
            "dataset1": [
                {"errors": [{"value": "issue1"}]},
                {"errors": [{"error": "Column not found in data"}]},
            ]
        }
        real, exec_ = CoreValidator._classify_errors(results)
        assert len(real) == 1
        assert len(exec_) == 1


class TestCoreValidatorExtractCTVersions:
    """Tests for the static _extract_ct_versions method."""

    def test_extracts_versions(self):
        from usdm4.core.core_validator import CoreValidator

        data = {
            "study": {
                "versions": [
                    {
                        "codes": [
                            {"codeSystemVersion": "2025-09-26"},
                            {"codeSystemVersion": "2024-03-29"},
                        ]
                    }
                ]
            }
        }
        versions = CoreValidator._extract_ct_versions(data)
        assert versions == {"2025-09-26", "2024-03-29"}

    def test_empty_data(self):
        from usdm4.core.core_validator import CoreValidator

        assert CoreValidator._extract_ct_versions({}) == set()

    def test_deduplicates(self):
        from usdm4.core.core_validator import CoreValidator

        data = {
            "a": {"codeSystemVersion": "2025-09-26"},
            "b": {"codeSystemVersion": "2025-09-26"},
        }
        versions = CoreValidator._extract_ct_versions(data)
        assert len(versions) == 1
