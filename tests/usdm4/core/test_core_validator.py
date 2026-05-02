"""Tests for CoreValidator — mocked to avoid cdisc-rules-engine runtime."""

import json
import os
import sys
from pathlib import Path
from threading import Lock
from unittest.mock import MagicMock, patch

import pytest

from usdm4.core.core_validation_result import CoreValidationResult


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def cache_dir(tmp_path):
    return str(tmp_path / "cache")


@pytest.fixture
def validator(cache_dir):
    from usdm4.core.core_validator import CoreValidator

    return CoreValidator(cache_dir=cache_dir, api_key="test-key-123")


@pytest.fixture
def usdm_file(tmp_path):
    """Create a minimal valid USDM JSON file."""
    f = tmp_path / "study.json"
    f.write_text(json.dumps({"study": {"name": "Test"}}))
    return str(f)


@pytest.fixture
def engine_mocks():
    """
    Build a dict that mimics what _import_engine() returns, with all
    CRE classes replaced by mocks.
    """
    # Fake cache service with dataset_cache and lock
    fake_cache = MagicMock()
    fake_cache.dataset_cache = {}
    fake_cache.dataset_cache_lock = Lock()
    fake_cache.get.return_value = None
    fake_cache.get_all_by_prefix.return_value = None
    fake_cache.add = MagicMock()

    fake_cache_factory_instance = MagicMock()
    fake_cache_factory_instance.get_cache_service.return_value = fake_cache

    FakeCacheServiceFactory = MagicMock(return_value=fake_cache_factory_instance)

    # Fake RulesEngine
    fake_data_service = MagicMock()
    fake_data_service.get_datasets.return_value = {"dataset": []}
    fake_rules_engine = MagicMock()
    fake_rules_engine.data_service = fake_data_service
    fake_rules_engine.validate_single_rule.return_value = {}
    FakeRulesEngine = MagicMock(return_value=fake_rules_engine)

    FakeCDISCLibraryService = MagicMock()
    FakeLibraryMetadataContainer = MagicMock()

    fake_get_rules_cache_key = MagicMock(return_value="usdm/4-0")

    # Use tmp_path from the calling test via a settable attribute
    fake_package_dir = Path("/tmp/fake_cdisc_engine")

    return {
        "package_dir": fake_package_dir,
        "config": MagicMock(),
        "CacheServiceFactory": FakeCacheServiceFactory,
        "RulesEngine": FakeRulesEngine,
        "get_rules_cache_key": fake_get_rules_cache_key,
        "CDISCLibraryService": FakeCDISCLibraryService,
        "PUBLISHED_CT_PACKAGES": "published_ct_packages",
        "LibraryMetadataContainer": FakeLibraryMetadataContainer,
        # expose internals for assertions
        "_cache": fake_cache,
        "_rules_engine": fake_rules_engine,
    }


# ------------------------------------------------------------------
# __init__ — line 76: sets env var when not present
# ------------------------------------------------------------------


class TestInitSetsEnvVar:
    def test_sets_env_var_when_missing(self, cache_dir):
        from usdm4.core.core_validator import CoreValidator

        env = {k: v for k, v in os.environ.items() if k != "CDISC_LIBRARY_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            CoreValidator(cache_dir=cache_dir, api_key="my-key")
            assert os.environ["CDISC_LIBRARY_API_KEY"] == "my-key"

    def test_does_not_overwrite_existing_env_var(self, cache_dir):
        from usdm4.core.core_validator import CoreValidator

        with patch.dict(os.environ, {"CDISC_LIBRARY_API_KEY": "existing"}, clear=False):
            CoreValidator(cache_dir=cache_dir, api_key="new-key")
            assert os.environ["CDISC_LIBRARY_API_KEY"] == "existing"


# ------------------------------------------------------------------
# validate() — line 105
# ------------------------------------------------------------------


class TestValidateMethod:
    def test_validate_delegates_to_execute_validation(self, validator, usdm_file):
        fake_result = CoreValidationResult(file_path=usdm_file)
        with patch.object(
            validator, "_execute_validation", return_value=fake_result
        ) as mock:
            result = validator.validate(usdm_file, version="4-0")
        mock.assert_called_once_with(usdm_file, "4-0")
        assert result is fake_result


# ------------------------------------------------------------------
# _execute_validation — lines 117–151
# ------------------------------------------------------------------


class TestExecuteValidation:
    def test_restores_cwd_on_success(self, validator, usdm_file):
        """CWD should be restored after validation, even with mocked engine."""
        original_cwd = os.getcwd()
        fake_result = CoreValidationResult()
        with (
            patch.object(validator, "_validate_file"),
            patch.object(
                validator,
                "_import_engine",
                return_value={
                    "package_dir": Path(original_cwd),
                },
            ),
            patch.object(validator, "_ensure_engine_resources"),
            patch.object(validator, "_run_validation", return_value=fake_result),
            patch.object(validator._cache_manager, "ensure_resources"),
            patch.object(validator._cache_manager, "prepare"),
        ):
            result = validator._execute_validation(usdm_file, "4-0")
        assert os.getcwd() == original_cwd
        assert result is fake_result

    def test_restores_cwd_on_failure(self, validator, usdm_file):
        """CWD should be restored even when validation raises."""
        original_cwd = os.getcwd()
        with (
            patch.object(validator, "_validate_file"),
            patch.object(
                validator,
                "_import_engine",
                return_value={
                    "package_dir": Path(original_cwd),
                },
            ),
            patch.object(validator, "_ensure_engine_resources"),
            patch.object(
                validator, "_run_validation", side_effect=RuntimeError("boom")
            ),
            patch.object(validator._cache_manager, "ensure_resources"),
            patch.object(validator._cache_manager, "prepare"),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                validator._execute_validation(usdm_file, "4-0")
        assert os.getcwd() == original_cwd

    def test_calls_preparation_steps(self, validator, usdm_file):
        """Should call ensure_resources, prepare, ensure_engine_resources."""
        original_cwd = os.getcwd()
        with (
            patch.object(validator, "_validate_file") as mock_vf,
            patch.object(
                validator,
                "_import_engine",
                return_value={
                    "package_dir": Path(original_cwd),
                },
            ) as mock_ie,
            patch.object(validator, "_ensure_engine_resources") as mock_eer,
            patch.object(
                validator, "_run_validation", return_value=CoreValidationResult()
            ),
            patch.object(validator._cache_manager, "ensure_resources") as mock_er,
            patch.object(validator._cache_manager, "prepare") as mock_pr,
        ):
            validator._execute_validation(usdm_file, "4-0")
        mock_vf.assert_called_once()
        mock_ie.assert_called_once()
        mock_er.assert_called_once()
        mock_pr.assert_called_once_with(version="4-0", api_key="test-key-123")
        mock_eer.assert_called_once()


# ------------------------------------------------------------------
# _ensure_engine_resources — lines 208–237
# ------------------------------------------------------------------


class TestEnsureEngineResources:
    def test_copies_jsonata_files(self, validator, tmp_path):
        """JSONata files from cache should be copied into the engine dir."""
        # Set up cached JSONata files
        src_jsonata = validator._cache_manager.jsonata_dir
        src_jsonata.mkdir(parents=True, exist_ok=True)
        (src_jsonata / "parse_refs.jsonata").write_text("// parse_refs")
        (src_jsonata / "sift_tree.jsonata").write_text("// sift_tree")

        # Target engine dir
        engine_dir = tmp_path / "engine_pkg"
        engine_dir.mkdir()

        validator._ensure_engine_resources(engine_dir)

        dst_jsonata = engine_dir / "resources" / "jsonata"
        assert (dst_jsonata / "parse_refs.jsonata").exists()
        assert (dst_jsonata / "sift_tree.jsonata").exists()

    def test_copies_xsd_files(self, validator, tmp_path):
        """XSD schema files from cache should be copied into the engine dir."""
        # Set up cached XSD files
        src_xsd = validator._cache_manager.schema_dir / "cdisc-usdm-xhtml-1.0"
        src_xsd.mkdir(parents=True, exist_ok=True)
        (src_xsd / "usdm-xhtml-1.0.xsd").write_text("<schema/>")

        engine_dir = tmp_path / "engine_pkg"
        engine_dir.mkdir()

        validator._ensure_engine_resources(engine_dir)

        dst_xsd = engine_dir / "resources" / "schema" / "xml" / "cdisc-usdm-xhtml-1.0"
        assert (dst_xsd / "usdm-xhtml-1.0.xsd").exists()

    def test_does_not_overwrite_existing(self, validator, tmp_path):
        """Files already in the engine dir should not be overwritten."""
        src_jsonata = validator._cache_manager.jsonata_dir
        src_jsonata.mkdir(parents=True, exist_ok=True)
        (src_jsonata / "parse_refs.jsonata").write_text("new content")

        engine_dir = tmp_path / "engine_pkg"
        dst_jsonata = engine_dir / "resources" / "jsonata"
        dst_jsonata.mkdir(parents=True, exist_ok=True)
        (dst_jsonata / "parse_refs.jsonata").write_text("original content")

        validator._ensure_engine_resources(engine_dir)

        assert (dst_jsonata / "parse_refs.jsonata").read_text() == "original content"

    def test_no_op_when_no_cached_resources(self, validator, tmp_path):
        """Should do nothing if no cached resources exist."""
        engine_dir = tmp_path / "engine_pkg"
        engine_dir.mkdir()
        validator._ensure_engine_resources(engine_dir)
        # No resources dir should be created
        assert not (engine_dir / "resources" / "jsonata").exists()


# ------------------------------------------------------------------
# _run_validation — lines 247–253 (stdout suppression)
# ------------------------------------------------------------------


class TestRunValidation:
    def test_suppresses_and_restores_stdout(self, validator, engine_mocks):
        """stdout/stderr should be redirected during validation and restored."""
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        def check_suppressed(*args, **kwargs):
            # During execution, stdout should be a StringIO
            assert sys.stdout is not original_stdout
            assert sys.stderr is not original_stderr
            return CoreValidationResult()

        with patch.object(
            validator, "_run_validation_inner", side_effect=check_suppressed
        ):
            validator._run_validation("/fake.json", "4-0", engine_mocks)

        assert sys.stdout is original_stdout
        assert sys.stderr is original_stderr

    def test_restores_stdout_on_error(self, validator, engine_mocks):
        """stdout/stderr should be restored even if inner validation raises."""
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        with patch.object(
            validator, "_run_validation_inner", side_effect=RuntimeError("inner")
        ):
            with pytest.raises(RuntimeError):
                validator._run_validation("/fake.json", "4-0", engine_mocks)

        assert sys.stdout is original_stdout
        assert sys.stderr is original_stderr


# ------------------------------------------------------------------
# _run_validation_inner — lines 262–365
# ------------------------------------------------------------------


class TestRunValidationInner:
    def test_resets_singletons(self, validator, engine_mocks, usdm_file):
        """Should clear dataset_cache and reset USDMDataService._instance."""
        cache = engine_mocks["_cache"]
        cache.dataset_cache["stale"] = "data"

        # Mock USDMDataService at module level
        fake_usdm_ds = MagicMock()
        fake_usdm_ds._instance = "stale_instance"

        # Provide empty rules so the rule loop is skipped
        with (
            patch.object(validator, "_load_ct_packages", return_value=[]),
            patch.object(validator, "_extract_ct_versions", return_value=set()),
            patch.object(validator, "_load_ct_data", return_value=({}, [])),
            patch.object(validator, "_load_rules", return_value=[]),
            patch(
                "usdm4.core.core_validator.USDMDataService", fake_usdm_ds, create=True
            ),
            patch(
                "cdisc_rules_engine.services.data_services.USDMDataService",
                fake_usdm_ds,
            ),
        ):
            result = validator._run_validation_inner(usdm_file, "4-0", engine_mocks)

        assert cache.dataset_cache == {}
        assert fake_usdm_ds._instance is None
        assert isinstance(result, CoreValidationResult)

    def test_returns_early_when_no_rules(self, validator, engine_mocks, usdm_file):
        """When no rules are loaded, should return an empty result."""
        fake_usdm_ds = MagicMock()
        fake_usdm_ds._instance = None

        with (
            patch.object(validator, "_load_ct_packages", return_value=[]),
            patch.object(validator, "_extract_ct_versions", return_value=set()),
            patch.object(validator, "_load_ct_data", return_value=({}, [])),
            patch.object(validator, "_load_rules", return_value=[]),
            patch(
                "cdisc_rules_engine.services.data_services.USDMDataService",
                fake_usdm_ds,
            ),
        ):
            result = validator._run_validation_inner(usdm_file, "4-0", engine_mocks)

        assert result.is_valid
        assert result.finding_count == 0

    def test_executes_rules_and_collects_findings(
        self, validator, engine_mocks, usdm_file
    ):
        """Rules returning errors should appear as findings in the result."""
        rules = [
            {
                "core_id": "CORE-001",
                "description": "Rule 1",
                "actions": [{"params": {"message": "Msg 1"}}],
            },
            {
                "core_id": "CORE-002",
                "description": "Rule 2",
                "actions": [{"params": {"message": "Msg 2"}}],
            },
        ]

        # First rule returns a finding, second returns nothing
        def validate_rule_side_effect(rule):
            if rule["core_id"] == "CORE-001":
                return {"ds": {"errors": [{"value": "bad_data"}]}}
            return {}

        engine_mocks[
            "_rules_engine"
        ].validate_single_rule.side_effect = validate_rule_side_effect

        fake_usdm_ds = MagicMock()
        fake_usdm_ds._instance = None

        with (
            patch.object(validator, "_load_ct_packages", return_value=[]),
            patch.object(validator, "_extract_ct_versions", return_value=set()),
            patch.object(validator, "_load_ct_data", return_value=({}, [])),
            patch.object(validator, "_load_rules", return_value=rules),
            patch(
                "cdisc_rules_engine.services.data_services.USDMDataService",
                fake_usdm_ds,
            ),
        ):
            result = validator._run_validation_inner(usdm_file, "4-0", engine_mocks)

        assert result.rules_executed == 2
        assert len(result.findings) == 1
        assert result.findings[0].rule_id == "CORE-001"

    def test_skips_excluded_rules(self, validator, engine_mocks, usdm_file):
        """Rules in _EXCLUDED_RULES should be skipped and counted."""
        rules = [
            {"core_id": "CORE-000955", "description": "Buggy rule", "actions": []},
            {
                "core_id": "CORE-100",
                "description": "Good rule",
                "actions": [{"params": {"message": "OK"}}],
            },
        ]

        engine_mocks["_rules_engine"].validate_single_rule.return_value = {}
        fake_usdm_ds = MagicMock()
        fake_usdm_ds._instance = None

        with (
            patch.object(validator, "_load_ct_packages", return_value=[]),
            patch.object(validator, "_extract_ct_versions", return_value=set()),
            patch.object(validator, "_load_ct_data", return_value=({}, [])),
            patch.object(validator, "_load_rules", return_value=rules),
            patch(
                "cdisc_rules_engine.services.data_services.USDMDataService",
                fake_usdm_ds,
            ),
        ):
            result = validator._run_validation_inner(usdm_file, "4-0", engine_mocks)

        assert result.rules_skipped == 1
        assert result.rules_executed == 1  # 2 rules - 1 skipped

    def test_rule_crash_becomes_execution_error(
        self, validator, engine_mocks, usdm_file
    ):
        """If a rule raises an exception, it should be captured as an execution error."""
        rules = [
            {
                "core_id": "CORE-099",
                "description": "Crashing rule",
                "actions": [{"params": {"message": "Crash"}}],
            },
        ]

        engine_mocks["_rules_engine"].validate_single_rule.side_effect = RuntimeError(
            "JSONata NoneType"
        )
        fake_usdm_ds = MagicMock()
        fake_usdm_ds._instance = None

        with (
            patch.object(validator, "_load_ct_packages", return_value=[]),
            patch.object(validator, "_extract_ct_versions", return_value=set()),
            patch.object(validator, "_load_ct_data", return_value=({}, [])),
            patch.object(validator, "_load_rules", return_value=rules),
            patch(
                "cdisc_rules_engine.services.data_services.USDMDataService",
                fake_usdm_ds,
            ),
        ):
            result = validator._run_validation_inner(usdm_file, "4-0", engine_mocks)

        assert len(result.execution_errors) == 1
        assert result.execution_errors[0]["rule_id"] == "CORE-099"
        assert result.is_valid  # crash is not a finding

    def test_separates_execution_errors_from_findings(
        self, validator, engine_mocks, usdm_file
    ):
        """Mixed real errors and execution errors should be separated."""
        rules = [
            {
                "core_id": "CORE-010",
                "description": "Mixed rule",
                "actions": [{"params": {"message": "Mixed"}}],
            },
        ]

        engine_mocks["_rules_engine"].validate_single_rule.return_value = {
            "ds": {
                "errors": [
                    {"value": "real_issue"},
                    {"error": "Column not found in data"},
                ]
            }
        }
        fake_usdm_ds = MagicMock()
        fake_usdm_ds._instance = None

        with (
            patch.object(validator, "_load_ct_packages", return_value=[]),
            patch.object(validator, "_extract_ct_versions", return_value=set()),
            patch.object(validator, "_load_ct_data", return_value=({}, [])),
            patch.object(validator, "_load_rules", return_value=rules),
            patch(
                "cdisc_rules_engine.services.data_services.USDMDataService",
                fake_usdm_ds,
            ),
        ):
            result = validator._run_validation_inner(usdm_file, "4-0", engine_mocks)

        assert len(result.findings) == 1
        assert result.findings[0].error_count == 1
        assert len(result.execution_errors) == 1

    def test_action_message_extraction(self, validator, engine_mocks, usdm_file):
        """Should extract message from actions[0].params.message."""
        rules = [
            {
                "core_id": "CORE-020",
                "description": "Desc",
                "actions": [
                    {"params": {"message": "Custom action message"}},
                    {"params": {"message": "Ignored second action"}},
                ],
            },
        ]

        engine_mocks["_rules_engine"].validate_single_rule.return_value = {
            "ds": {"errors": [{"value": "x"}]}
        }
        fake_usdm_ds = MagicMock()
        fake_usdm_ds._instance = None

        with (
            patch.object(validator, "_load_ct_packages", return_value=[]),
            patch.object(validator, "_extract_ct_versions", return_value=set()),
            patch.object(validator, "_load_ct_data", return_value=({}, [])),
            patch.object(validator, "_load_rules", return_value=rules),
            patch(
                "cdisc_rules_engine.services.data_services.USDMDataService",
                fake_usdm_ds,
            ),
        ):
            result = validator._run_validation_inner(usdm_file, "4-0", engine_mocks)

        assert result.findings[0].message == "Custom action message"

    def test_rule_with_no_actions(self, validator, engine_mocks, usdm_file):
        """Rules with empty or missing actions should still work."""
        rules = [
            {"core_id": "CORE-030", "description": "No actions"},
            {
                "core_id": "CORE-031",
                "description": "Empty actions",
                "actions": [],
            },
        ]

        engine_mocks["_rules_engine"].validate_single_rule.return_value = {
            "ds": {"errors": [{"value": "x"}]}
        }
        fake_usdm_ds = MagicMock()
        fake_usdm_ds._instance = None

        with (
            patch.object(validator, "_load_ct_packages", return_value=[]),
            patch.object(validator, "_extract_ct_versions", return_value=set()),
            patch.object(validator, "_load_ct_data", return_value=({}, [])),
            patch.object(validator, "_load_rules", return_value=rules),
            patch(
                "cdisc_rules_engine.services.data_services.USDMDataService",
                fake_usdm_ds,
            ),
        ):
            result = validator._run_validation_inner(usdm_file, "4-0", engine_mocks)

        assert len(result.findings) == 2
        assert result.findings[0].message == ""
        assert result.findings[1].message == ""


# ------------------------------------------------------------------
# _load_ct_packages — lines 376–400
# ------------------------------------------------------------------


class TestLoadCtPackages:
    def test_returns_disk_cache(self, validator):
        """Should return from disk cache when available."""

        cache = MagicMock()
        packages = ["sdtmct-2025-09-26", "ddfct-2025-09-26"]
        validator._cache_manager.cache_ct_packages(packages)

        result = validator._load_ct_packages(cache, MagicMock, "published_ct_packages")
        assert result == packages
        cache.add.assert_called_once_with("published_ct_packages", packages)

    def test_returns_memory_cache(self, validator):
        """Should fall back to in-memory cache when disk cache is empty."""
        cache = MagicMock()
        cache.get.return_value = ["sdtmct-2025-09-26"]

        result = validator._load_ct_packages(cache, MagicMock, "published_ct_packages")
        assert result == ["sdtmct-2025-09-26"]

    def test_downloads_when_no_cache(self, validator):
        """Should download from CDISC Library when both caches miss."""
        cache = MagicMock()
        cache.get.return_value = None

        fake_library = MagicMock()
        fake_library.get_all_ct_packages.return_value = [
            {"href": "/ct/sdtmct-2025-09-26"},
            {"href": "/ct/ddfct-2025-09-26"},
        ]
        FakeLibraryService = MagicMock(return_value=fake_library)

        result = validator._load_ct_packages(
            cache, FakeLibraryService, "published_ct_packages"
        )
        assert "sdtmct-2025-09-26" in result
        assert "ddfct-2025-09-26" in result

    def test_returns_empty_without_api_key(self, cache_dir):
        """Without an API key, should return empty list."""
        from usdm4.core.core_validator import CoreValidator

        env = {k: v for k, v in os.environ.items() if k != "CDISC_LIBRARY_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            v = CoreValidator(cache_dir=cache_dir, api_key="")
            cache = MagicMock()
            cache.get.return_value = None
            result = v._load_ct_packages(cache, MagicMock, "published_ct_packages")
        assert result == []

    def test_handles_download_failure(self, validator):
        """Download failure should return empty list, not raise."""
        cache = MagicMock()
        cache.get.return_value = None

        fake_library = MagicMock()
        fake_library.get_all_ct_packages.side_effect = Exception("Network error")
        FakeLibraryService = MagicMock(return_value=fake_library)

        result = validator._load_ct_packages(
            cache, FakeLibraryService, "published_ct_packages"
        )
        assert result == []


# ------------------------------------------------------------------
# _load_ct_data — lines 410–449
# ------------------------------------------------------------------


class TestLoadCtData:
    def test_returns_empty_when_no_versions(self, validator):
        """No CT versions needed → empty result."""
        cache = MagicMock()
        metadata, loaded = validator._load_ct_data(
            cache, MagicMock, ["sdtmct-2025-09-26"], set()
        )
        assert metadata == {}
        assert loaded == []

    def test_loads_from_disk_cache(self, validator):
        """Should use disk cache when available."""
        cache = MagicMock()
        ct_packages = ["sdtmct-2025-09-26", "ddfct-2025-09-26"]

        # Pre-populate disk cache for one package
        validator._cache_manager.cache_ct_package_data(
            "sdtmct-2025-09-26", {"C1": {"code": "M"}}
        )

        metadata, loaded = validator._load_ct_data(
            cache, MagicMock, ct_packages, {"2025-09-26"}
        )
        assert "sdtmct-2025-09-26" in metadata
        assert "sdtmct-2025-09-26" in loaded

    def test_downloads_when_not_cached(self, validator):
        """Should download from CDISC Library when not on disk."""
        cache = MagicMock()
        ct_packages = ["sdtmct-2025-09-26"]

        fake_library = MagicMock()
        fake_library.get_codelist_terms_map.return_value = {"C1": {"code": "M"}}
        FakeLibraryService = MagicMock(return_value=fake_library)

        metadata, loaded = validator._load_ct_data(
            cache, FakeLibraryService, ct_packages, {"2025-09-26"}
        )
        assert "sdtmct-2025-09-26" in metadata
        assert "sdtmct-2025-09-26" in loaded

    def test_skips_non_matching_packages(self, validator):
        """Packages not in ct_packages list should be skipped."""
        cache = MagicMock()
        ct_packages = ["sdtmct-2025-09-26"]  # no ddfct

        metadata, loaded = validator._load_ct_data(
            cache, MagicMock, ct_packages, {"2025-09-26"}
        )
        # sdtmct isn't on disk, no api key to download → not loaded
        # but ddfct shouldn't even be attempted
        assert "ddfct-2025-09-26" not in loaded

    def test_handles_download_failure(self, validator):
        """Download failure for one package should not prevent others."""
        cache = MagicMock()
        ct_packages = ["sdtmct-2025-09-26", "ddfct-2025-09-26"]

        fake_library = MagicMock()
        fake_library.get_codelist_terms_map.side_effect = [
            Exception("timeout"),
            {"C2": {"code": "F"}},
        ]
        FakeLibraryService = MagicMock(return_value=fake_library)

        metadata, loaded = validator._load_ct_data(
            cache, FakeLibraryService, ct_packages, {"2025-09-26"}
        )
        # First package failed, second succeeded
        assert "ddfct-2025-09-26" in loaded
        assert "sdtmct-2025-09-26" not in loaded

    def test_no_download_without_api_key(self, cache_dir):
        """Without API key, should skip download attempts."""
        from usdm4.core.core_validator import CoreValidator

        env = {k: v for k, v in os.environ.items() if k != "CDISC_LIBRARY_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            v = CoreValidator(cache_dir=cache_dir, api_key="")
            cache = MagicMock()
            metadata, loaded = v._load_ct_data(
                cache, MagicMock, ["sdtmct-2025-09-26"], {"2025-09-26"}
            )
        assert metadata == {}
        assert loaded == []


# ------------------------------------------------------------------
# _load_rules — lines 455–493
# ------------------------------------------------------------------


class TestLoadRules:
    def test_loads_from_disk_cache(self, validator):
        """Should return rules from disk cache and populate in-memory cache."""
        cache = MagicMock()
        get_rules_cache_key = MagicMock(return_value="usdm/4-0")

        # Pre-populate disk cache
        rules = [{"core_id": "CORE-001"}, {"core_id": "CORE-002"}]
        validator._cache_manager.cache_rules("usdm", "4-0", rules)

        result = validator._load_rules(cache, MagicMock, get_rules_cache_key, "4-0")
        assert len(result) == 2
        assert cache.add.call_count == 2  # one per rule

    def test_loads_from_memory_cache(self, validator):
        """Should fall back to in-memory cache when disk is empty."""
        rules = [{"core_id": "CORE-001"}]
        cache = MagicMock()
        cache.get_all_by_prefix.return_value = rules
        get_rules_cache_key = MagicMock(return_value="usdm/4-0")

        result = validator._load_rules(cache, MagicMock, get_rules_cache_key, "4-0")
        assert result == rules

    def test_downloads_when_not_cached(self, validator):
        """Should download from CDISC Library when both caches miss."""
        cache = MagicMock()
        cache.get_all_by_prefix.return_value = None
        get_rules_cache_key = MagicMock(return_value="usdm/4-0")

        downloaded_rules = [{"core_id": "CORE-001"}, {"core_id": "CORE-002"}]
        fake_library = MagicMock()
        fake_library.get_rules_by_catalog.return_value = {"rules": downloaded_rules}
        FakeLibraryService = MagicMock(return_value=fake_library)

        result = validator._load_rules(
            cache, FakeLibraryService, get_rules_cache_key, "4-0"
        )
        assert len(result) == 2
        # Should persist to disk
        assert validator._cache_manager.load_cached_rules("usdm", "4-0") is not None

    def test_returns_empty_without_api_key(self, cache_dir):
        """Without API key, should return empty list."""
        from usdm4.core.core_validator import CoreValidator

        env = {k: v for k, v in os.environ.items() if k != "CDISC_LIBRARY_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            v = CoreValidator(cache_dir=cache_dir, api_key="")
            cache = MagicMock()
            cache.get_all_by_prefix.return_value = None
            get_rules_cache_key = MagicMock(return_value="usdm/4-0")
            result = v._load_rules(cache, MagicMock, get_rules_cache_key, "4-0")
        assert result == []

    def test_handles_download_failure(self, validator):
        """Download failure should return empty list."""
        cache = MagicMock()
        cache.get_all_by_prefix.return_value = None
        get_rules_cache_key = MagicMock(return_value="usdm/4-0")

        fake_library = MagicMock()
        fake_library.get_rules_by_catalog.side_effect = Exception("API error")
        FakeLibraryService = MagicMock(return_value=fake_library)

        result = validator._load_rules(
            cache, FakeLibraryService, get_rules_cache_key, "4-0"
        )
        assert result == []

    def test_handles_non_dict_response(self, validator):
        """Should handle case where get_rules_by_catalog returns a list directly."""
        cache = MagicMock()
        cache.get_all_by_prefix.return_value = None
        get_rules_cache_key = MagicMock(return_value="usdm/4-0")

        downloaded_rules = [{"core_id": "CORE-001"}]
        fake_library = MagicMock()
        fake_library.get_rules_by_catalog.return_value = downloaded_rules
        FakeLibraryService = MagicMock(return_value=fake_library)

        result = validator._load_rules(
            cache, FakeLibraryService, get_rules_cache_key, "4-0"
        )
        assert len(result) == 1


# ------------------------------------------------------------------
# _classify_errors — line 527 (non-dict items skipped)
# ------------------------------------------------------------------


class TestClassifyErrorsEdgeCases:
    def test_non_dict_items_are_skipped(self):
        """Non-dict items in the results list should be silently skipped."""
        from usdm4.core.core_validator import CoreValidator

        results = {
            "dataset": [
                "not a dict",
                42,
                {"errors": [{"value": "real"}]},
            ]
        }
        real, exec_ = CoreValidator._classify_errors(results)
        assert len(real) == 1
        assert real[0]["value"] == "real"

    def test_outside_scope_is_execution_error(self):
        """'Outside scope' should be classified as execution error."""
        from usdm4.core.core_validator import CoreValidator

        results = {"ds": {"errors": [{"error": "Outside scope"}]}}
        real, exec_ = CoreValidator._classify_errors(results)
        assert len(real) == 0
        assert len(exec_) == 1

    def test_operation_execution_error_is_execution_error(self):
        """'Error occurred during operation execution' should be classified as
        execution error.

        Added after a corpus run surfaced thousands of false 'findings' caused
        by a pandas merge bug inside the rules engine — those errors are not
        validation findings and must not surface as such.
        """
        from usdm4.core.core_validator import CoreValidator

        results = {
            "ds": {
                "errors": [
                    {"error": "Error occurred during operation execution"},
                ]
            }
        }
        real, exec_ = CoreValidator._classify_errors(results)
        assert len(real) == 0
        assert len(exec_) == 1

    def test_non_dict_errors_are_real(self):
        """Non-dict error entries should be treated as real errors."""
        from usdm4.core.core_validator import CoreValidator

        results = {"ds": {"errors": ["string error"]}}
        real, exec_ = CoreValidator._classify_errors(results)
        assert len(real) == 1
        assert real[0] == "string error"
