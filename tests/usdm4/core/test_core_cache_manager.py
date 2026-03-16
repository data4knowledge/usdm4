"""Tests for CoreCacheManager."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from usdm4.core.core_cache_manager import CoreCacheManager


@pytest.fixture
def cache_dir(tmp_path):
    """Provide a temporary cache directory."""
    return str(tmp_path / "test_cache")


@pytest.fixture
def manager(cache_dir):
    """Provide a CoreCacheManager with a temp directory."""
    return CoreCacheManager(cache_dir)


class TestCoreCacheManager:
    def test_creates_cache_dir(self, cache_dir):
        mgr = CoreCacheManager(cache_dir)
        assert Path(cache_dir).exists()

    def test_default_cache_dir(self):
        mgr = CoreCacheManager()
        expected = Path.home() / ".cache" / "usdm4" / "core"
        assert mgr.cache_dir == expected

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
