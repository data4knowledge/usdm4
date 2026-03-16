"""
CDISC CORE validation for USDM JSON files.

Wraps the cdisc-rules-engine to validate USDM files against the full set
of CDISC CORE conformance rules. Provides both synchronous and asynchronous
(background) execution, with a configurable persistent cache for rules,
CT packages, and schema resources.

Usage:
    from usdm4.core import CoreValidator

    # Synchronous
    validator = CoreValidator()
    result = validator.validate("study.json")
    print(result.format_text())

    # Asynchronous (background)
    future = validator.validate_async("study.json")
    # ... do other work ...
    result = future.result()  # blocks until done
"""

import io
import json
import logging
import os
import sys
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from usdm4.core.core_cache_manager import CoreCacheManager
from usdm4.core.core_validation_result import CoreRuleFinding, CoreValidationResult

logger = logging.getLogger(__name__)

# Rules known to have bugs in the CORE engine (JSONata/NoneType errors).
# These are excluded from execution to avoid crashes.
_EXCLUDED_RULES = {
    "CORE-000955",  # JSONata bug
    "CORE-000956",  # JSONata bug
}

# Sentinel for execution errors (not real data issues)
_EXECUTION_ERROR_TYPES = {
    "Column not found in data",
    "Error occurred during dataset preprocessing",
}

# Thread pool shared by all CoreValidator instances for background work.
# A single-thread pool serialises validation runs, which is appropriate
# because the CDISC Rules Engine is not thread-safe (it mutates globals
# like os.getcwd and sys.stdout).
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="usdm4-core")


class CoreValidator:
    """
    Validates USDM JSON files using the CDISC Rules Engine (CORE).

    Args:
        cache_dir: Path to the persistent cache directory for downloaded
            resources (rules, CT packages, schemas). If None, defaults
            to ``~/.cache/usdm4/core/``.
        api_key: CDISC Library API key. If None, reads from the
            ``CDISC_LIBRARY_API_KEY`` or ``CDISC_API_KEY`` environment variable.

    Example::

        validator = CoreValidator(cache_dir="/tmp/my_cache")
        result = validator.validate("study.json", version="4-0")
        if not result.is_valid:
            print(result.format_text())
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self._cache_manager = CoreCacheManager(cache_dir)
        self._api_key = api_key or os.environ.get(
            "CDISC_LIBRARY_API_KEY", os.environ.get("CDISC_API_KEY", "")
        )
        # Ensure the API key env var is set for the rules engine
        if self._api_key and "CDISC_LIBRARY_API_KEY" not in os.environ:
            os.environ["CDISC_LIBRARY_API_KEY"] = self._api_key

    @property
    def cache_manager(self) -> CoreCacheManager:
        """Access the underlying cache manager (e.g. to clear the cache)."""
        return self._cache_manager

    def validate(
        self,
        file_path: str,
        version: str = "4-0",
    ) -> CoreValidationResult:
        """
        Validate a USDM JSON file synchronously.

        This may take several minutes depending on file size and whether
        resources need to be downloaded. For non-blocking execution, use
        :meth:`validate_async` instead.

        Args:
            file_path: Path to the USDM JSON file.
            version: USDM version string (``"3-0"`` or ``"4-0"``).

        Returns:
            A :class:`CoreValidationResult` with findings and metadata.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not valid JSON or not a USDM file.
        """
        return self._execute_validation(file_path, version)

    def validate_async(
        self,
        file_path: str,
        version: str = "4-0",
    ) -> Future:
        """
        Validate a USDM JSON file in a background thread.

        Returns immediately with a :class:`~concurrent.futures.Future` that
        will contain the :class:`CoreValidationResult` when validation completes.

        Args:
            file_path: Path to the USDM JSON file.
            version: USDM version string (``"3-0"`` or ``"4-0"``).

        Returns:
            A ``Future[CoreValidationResult]``. Call ``.result()`` to block
            until done, or use ``.add_done_callback(fn)`` to be notified.

        Example::

            future = validator.validate_async("study.json")
            future.add_done_callback(lambda f: print(f.result().format_text()))
        """
        return _executor.submit(self._execute_validation, file_path, version)

    # ------------------------------------------------------------------
    # Internal implementation
    # ------------------------------------------------------------------

    def _execute_validation(
        self,
        file_path: str,
        version: str,
    ) -> CoreValidationResult:
        """Core validation logic, run either synchronously or in a thread."""
        abs_path = os.path.abspath(file_path)

        # Validate the file can be loaded
        self._validate_file(abs_path)

        # Import cdisc-rules-engine components (deferred to avoid import-time
        # side effects until actually needed)
        engine_imports = self._import_engine()

        # Ensure resource files are available
        self._cache_manager.ensure_resources()

        # The CDISC Rules Engine expects a resources/ dir in CWD.
        # We need to set CWD to a location that has the resources.
        # Strategy: symlink our cached resources into the engine's package dir
        # or chdir to the cache dir.
        cdisc_package_dir = engine_imports["package_dir"]
        self._ensure_engine_resources(cdisc_package_dir)

        original_cwd = os.getcwd()
        original_log_level = logging.root.manager.disable

        # Suppress the engine's verbose output
        logging.disable(logging.CRITICAL)
        os.chdir(cdisc_package_dir)

        try:
            return self._run_validation(
                abs_path, version, engine_imports
            )
        finally:
            os.chdir(original_cwd)
            logging.disable(original_log_level)

    def _validate_file(self, abs_path: str) -> None:
        """Check that the file exists and is valid USDM JSON."""
        path = Path(abs_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {abs_path}")
        if not path.suffix.lower() == ".json":
            raise ValueError(f"Expected a JSON file, got: {path.suffix}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "study" not in data:
            raise ValueError(
                "Invalid USDM file: missing 'study' key. "
                "USDM JSON files must contain a 'study' object."
            )

    def _import_engine(self) -> dict:
        """
        Import cdisc-rules-engine components.

        Returns a dict of the needed classes/functions to avoid keeping
        them as module-level imports (which cause side effects on import).
        """
        import cdisc_rules_engine
        from cdisc_rules_engine.config import config
        from cdisc_rules_engine.constants.cache_constants import PUBLISHED_CT_PACKAGES
        from cdisc_rules_engine.models.library_metadata_container import (
            LibraryMetadataContainer,
        )
        from cdisc_rules_engine.rules_engine import RulesEngine
        from cdisc_rules_engine.services.cache import CacheServiceFactory
        from cdisc_rules_engine.services.cdisc_library_service import (
            CDISCLibraryService,
        )
        from cdisc_rules_engine.utilities.utils import get_rules_cache_key

        return {
            "package_dir": Path(cdisc_rules_engine.__file__).parent.parent,
            "config": config,
            "CacheServiceFactory": CacheServiceFactory,
            "RulesEngine": RulesEngine,
            "get_rules_cache_key": get_rules_cache_key,
            "CDISCLibraryService": CDISCLibraryService,
            "PUBLISHED_CT_PACKAGES": PUBLISHED_CT_PACKAGES,
            "LibraryMetadataContainer": LibraryMetadataContainer,
        }

    def _ensure_engine_resources(self, cdisc_package_dir: Path) -> None:
        """
        Copy or symlink cached resources into the engine's package directory
        so that the engine can find them at ``resources/`` relative to CWD.

        The engine resolves resource paths relative to os.getcwd(), which we
        set to cdisc_package_dir. We need our cached JSONata and XSD files
        to appear under cdisc_package_dir/resources/.
        """
        cache_resources = self._cache_manager.resources_dir
        engine_resources = cdisc_package_dir / "resources"

        # Copy JSONata files
        src_jsonata = cache_resources / "jsonata"
        dst_jsonata = engine_resources / "jsonata"
        if src_jsonata.exists():
            dst_jsonata.mkdir(parents=True, exist_ok=True)
            for f in src_jsonata.iterdir():
                dst = dst_jsonata / f.name
                if not dst.exists():
                    import shutil
                    shutil.copy2(f, dst)

        # Copy XSD schema files
        src_schema = cache_resources / "schema" / "xml"
        dst_schema = engine_resources / "schema" / "xml"
        if src_schema.exists():
            for subdir_name in ["cdisc-usdm-xhtml-1.0", "xhtml-1.1"]:
                src_subdir = src_schema / subdir_name
                dst_subdir = dst_schema / subdir_name
                if src_subdir.exists():
                    dst_subdir.mkdir(parents=True, exist_ok=True)
                    for f in src_subdir.iterdir():
                        dst = dst_subdir / f.name
                        if not dst.exists():
                            import shutil
                            shutil.copy2(f, dst)

    def _run_validation(
        self,
        abs_path: str,
        version: str,
        engine: dict,
    ) -> CoreValidationResult:
        """Internal validation logic with output suppression."""
        # Suppress stdout/stderr from the engine
        saved_stdout, saved_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = io.StringIO()

        try:
            return self._run_validation_inner(abs_path, version, engine)
        finally:
            sys.stdout, sys.stderr = saved_stdout, saved_stderr

    def _run_validation_inner(
        self,
        abs_path: str,
        version: str,
        engine: dict,
    ) -> CoreValidationResult:
        """The actual validation pipeline."""
        CacheServiceFactory = engine["CacheServiceFactory"]
        config = engine["config"]
        RulesEngine = engine["RulesEngine"]
        get_rules_cache_key = engine["get_rules_cache_key"]
        CDISCLibraryService = engine["CDISCLibraryService"]
        PUBLISHED_CT_PACKAGES = engine["PUBLISHED_CT_PACKAGES"]
        LibraryMetadataContainer = engine["LibraryMetadataContainer"]

        # Initialize the in-memory cache used by the rules engine
        cache = CacheServiceFactory(config).get_cache_service()

        # Load USDM data
        with open(abs_path, "r", encoding="utf-8") as f:
            usdm_data = json.load(f)

        # --- CT Package Setup ---
        ct_packages = self._load_ct_packages(cache, CDISCLibraryService, PUBLISHED_CT_PACKAGES)
        ct_versions_needed = self._extract_ct_versions(usdm_data)
        ct_package_metadata, loaded_packages = self._load_ct_data(
            cache, CDISCLibraryService, ct_packages, ct_versions_needed
        )

        library_metadata = LibraryMetadataContainer(
            published_ct_packages=ct_packages,
            ct_package_metadata=ct_package_metadata,
        )

        # --- Rules Engine Setup ---
        rules_engine = RulesEngine(
            cache=cache,
            standard="usdm",
            standard_version=version,
            dataset_paths=[abs_path],
            library_metadata=library_metadata,
        )
        datasets = rules_engine.data_service.get_datasets()

        # --- Load Rules ---
        rules = self._load_rules(
            cache, CDISCLibraryService, get_rules_cache_key, version
        )

        # --- Execute Rules ---
        result = CoreValidationResult(
            file_path=abs_path,
            version=version,
            ct_packages_available=len(ct_packages),
            ct_packages_loaded=loaded_packages,
        )

        if not rules:
            return result

        skipped = 0
        for rule in rules:
            rule_id = rule.get("core_id", "unknown")

            if rule_id in _EXCLUDED_RULES:
                skipped += 1
                continue

            description = rule.get("description", "")
            action_message = ""
            actions = rule.get("actions", [])
            if actions and isinstance(actions, list):
                params = actions[0].get("params", {})
                action_message = params.get("message", "")

            try:
                rule_results = rules_engine.validate_single_rule(rule, datasets)
                real_errors, exec_errors = self._classify_errors(rule_results)

                if real_errors:
                    result.findings.append(
                        CoreRuleFinding(
                            rule_id=rule_id,
                            description=description,
                            message=action_message,
                            errors=real_errors,
                        )
                    )
                result.execution_errors.extend(exec_errors)

            except Exception:
                # Rule crashed - treat as execution error
                result.execution_errors.append(
                    {"rule_id": rule_id, "error": "Rule execution crashed"}
                )

        result.rules_executed = len(rules) - skipped
        result.rules_skipped = skipped
        return result

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _load_ct_packages(self, cache, CDISCLibraryService, PUBLISHED_CT_PACKAGES) -> list:
        """Load the list of published CT packages, using disk cache if available."""
        # Try disk cache first
        cached = self._cache_manager.load_cached_ct_packages()
        if cached:
            cache.add(PUBLISHED_CT_PACKAGES, cached)
            return cached

        # Try in-memory cache
        cached = cache.get(PUBLISHED_CT_PACKAGES)
        if cached:
            return cached

        if not self._api_key:
            return []

        try:
            library_service = CDISCLibraryService(self._api_key, cache)
            packages = library_service.get_all_ct_packages()
            ct_packages = [
                package.get("href", "").split("/")[-1] for package in packages
            ]
            cache.add(PUBLISHED_CT_PACKAGES, ct_packages)
            # Persist to disk
            self._cache_manager.cache_ct_packages(ct_packages)
            return ct_packages
        except Exception:
            return []

    def _load_ct_data(
        self, cache, CDISCLibraryService, ct_packages: list, ct_versions: set
    ) -> tuple[dict, list]:
        """
        Load CT package codelist data for the versions used in the USDM file.

        Returns (ct_package_metadata dict, list of loaded package names).
        """
        ct_package_metadata = {}
        loaded_packages = []

        if not ct_versions:
            return ct_package_metadata, loaded_packages

        library_service = None

        for ct_version in ct_versions:
            for ct_type in ["sdtmct", "ddfct"]:
                package_name = f"{ct_type}-{ct_version}"
                if package_name not in ct_packages:
                    continue

                # Try disk cache first
                cached_data = self._cache_manager.load_cached_ct_package_data(package_name)
                if cached_data:
                    ct_package_metadata[package_name] = cached_data
                    loaded_packages.append(package_name)
                    continue

                # Download from CDISC Library
                if library_service is None:
                    if not self._api_key:
                        continue
                    library_service = CDISCLibraryService(self._api_key, cache)

                try:
                    ct_data = library_service.get_codelist_terms_map(package_name)
                    if ct_data:
                        ct_package_metadata[package_name] = ct_data
                        loaded_packages.append(package_name)
                        # Persist to disk
                        self._cache_manager.cache_ct_package_data(package_name, ct_data)
                except Exception:
                    pass

        return ct_package_metadata, loaded_packages

    def _load_rules(
        self, cache, CDISCLibraryService, get_rules_cache_key, version: str
    ) -> list:
        """Load validation rules, using disk cache → in-memory cache → CDISC Library."""
        cache_key = get_rules_cache_key("usdm", version)

        # Try disk cache first
        disk_rules = self._cache_manager.load_cached_rules("usdm", version)
        if disk_rules:
            # Also populate the in-memory cache for the engine
            for rule in disk_rules:
                rule_id = rule.get("core_id", "unknown")
                cache.add(f"{cache_key}/{rule_id}", rule)
            return disk_rules

        # Try in-memory cache
        rules = cache.get_all_by_prefix(cache_key)
        if rules:
            return rules

        # Download from CDISC Library
        if not self._api_key:
            return []

        try:
            library_service = CDISCLibraryService(self._api_key, cache)
            result = library_service.get_rules_by_catalog("usdm", version)
            rules = result.get("rules", []) if isinstance(result, dict) else result
            actual_key = result.get("key_prefix", cache_key) if isinstance(result, dict) else cache_key

            for rule in rules:
                rule_id = rule.get("core_id", "unknown")
                cache.add(f"{actual_key}/{rule_id}", rule)

            # Persist to disk
            self._cache_manager.cache_rules("usdm", version, rules)
            return rules
        except Exception:
            return []

    @staticmethod
    def _extract_ct_versions(usdm_data: dict) -> set:
        """Extract unique codeSystemVersion values from USDM data."""
        versions = set()

        def walk(obj):
            if isinstance(obj, dict):
                if "codeSystemVersion" in obj:
                    versions.add(obj["codeSystemVersion"])
                for value in obj.values():
                    walk(value)
            elif isinstance(obj, list):
                for item in obj:
                    walk(item)

        walk(usdm_data)
        return versions

    @staticmethod
    def _classify_errors(rule_results) -> tuple[list, list]:
        """
        Separate real validation findings from execution errors.

        Returns (real_errors, execution_errors).
        """
        real_errors = []
        exec_errors = []

        for val in (rule_results or {}).values():
            items = val if isinstance(val, list) else [val]
            for item in items:
                if not isinstance(item, dict):
                    continue
                for error in item.get("errors", []):
                    if isinstance(error, dict):
                        error_type = error.get("error", "")
                        if error_type in _EXECUTION_ERROR_TYPES:
                            exec_errors.append(error)
                            continue
                    real_errors.append(error)

        return real_errors, exec_errors
