"""
Cache manager for CDISC CORE validation resources.

Manages a configurable cache directory for storing downloaded resources
(JSONata files, XSD schemas, rules, CT packages) so they persist across
validation runs and package upgrades.

The default cache location is platform-appropriate:
- macOS:   ~/Library/Caches/usdm4/core/
- Windows: %LOCALAPPDATA%/usdm4/Cache/core/
- Linux:   ~/.cache/usdm4/core/
"""

import json
import logging
import os
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from platformdirs import user_cache_dir

logger = logging.getLogger(__name__)

# GitHub URLs for resources not included in the cdisc-rules-engine pip package
_GITHUB_RAW_BASE = "https://raw.githubusercontent.com/cdisc-org/cdisc-rules-engine/main"

_JSONATA_FILES = [
    "resources/jsonata/parse_refs.jsonata",
    "resources/jsonata/sift_tree.jsonata",
]

_USDM_XHTML_SCHEMA_FILES = [
    "resources/schema/xml/cdisc-usdm-xhtml-1.0/usdm-xhtml-1.0.xsd",
    "resources/schema/xml/cdisc-usdm-xhtml-1.0/usdm-xhtml-extension.xsd",
    "resources/schema/xml/cdisc-usdm-xhtml-1.0/usdm-xhtml-ns.xsd",
]

_XHTML_SCHEMA_FILES = [
    "resources/schema/xml/xhtml-1.1/aria-attributes-1.xsd",
    "resources/schema/xml/xhtml-1.1/xframes-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-access-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-applet-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-attribs-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-base-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-basic-form-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-basic-table-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-bdo-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-blkphras-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-blkpres-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-blkstruct-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-charent-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-csismap-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-datatypes-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-edit-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-events-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-form-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-frames-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-framework-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-hypertext-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-iframe-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-image-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-inlphras-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-inlpres-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-inlstruct-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-inlstyle-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-inputmode-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-legacy-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-legacy-redecl-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-link-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-list-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-meta-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-metaAttributes-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-misc-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-nameident-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-notations-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-object-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-param-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-pres-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-print-model-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-print.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-ruby-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-script-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-ssismap-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-struct-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-style-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-table-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-target-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-text-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-uri-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml11-flat.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml11-model-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml11-modules-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml11.xsd",
    "resources/schema/xml/xhtml-1.1/xml.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-basic10-model-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-basic10-modules-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-basic10.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-basic11-model-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-basic11-modules-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-basic11.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-lat1.ent",
    "resources/schema/xml/xhtml-1.1/xhtml-special.ent",
    "resources/schema/xml/xhtml-1.1/xhtml-symbol.ent",
    "resources/schema/xml/xhtml-1.1/xhtml1-frameset.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml1-strict.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml1-transitional.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-rdfa-model-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-rdfa-modules-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-rdfa-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-role-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-role-attrib-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-mobile10-model-1.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-mobile10.xsd",
    "resources/schema/xml/xhtml-1.1/xhtml-simple-1.xsd",
]


def default_cache_dir() -> Path:
    """Return the platform-appropriate default cache directory.

    - macOS:   ~/Library/Caches/usdm4/core/
    - Windows: %LOCALAPPDATA%/usdm4/Cache/core/
    - Linux:   ~/.cache/usdm4/core/  (respects $XDG_CACHE_HOME)
    """
    return Path(user_cache_dir("usdm4")) / "core"


@dataclass
class CacheStatus:
    """Result of a cache readiness check.

    Attributes:
        ready: ``True`` when all pre-fetchable resources are present.
        has_resources: JSONata and XSD schema files are present.
        has_rules: Validation rules for the requested version are cached.
        has_ct_index: The CT package index is cached.
        cache_dir: The resolved cache directory path.
        details: Human-readable list of what is missing (empty when ready).
    """

    ready: bool = False
    has_resources: bool = False
    has_rules: bool = False
    has_ct_index: bool = False
    cache_dir: str = ""
    details: list[str] = field(default_factory=list)


class CoreCacheManager:
    """
    Manages the local cache directory for CDISC CORE validation resources.

    Resources cached include:

    - JSONata custom function files (from GitHub, no API key needed)
    - XSD schema files — USDM XHTML + XHTML 1.1 (from GitHub, no API key needed)
    - Validation rules (from CDISC Library API, API key required)
    - CT package index and codelist data (from CDISC Library API, API key required)

    The cache directory is configurable.  The default location is
    platform-appropriate (see :func:`default_cache_dir`).

    Args:
        cache_dir: Path to the cache directory.  If ``None``, uses the
            platform default.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is not None:
            self._cache_dir = Path(cache_dir)
        else:
            self._cache_dir = default_cache_dir()
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Directory layout
    # ------------------------------------------------------------------

    @property
    def cache_dir(self) -> Path:
        """The root cache directory path."""
        return self._cache_dir

    @property
    def resources_dir(self) -> Path:
        """The resources directory within the cache (mirrors site-packages layout)."""
        return self._cache_dir / "resources"

    @property
    def jsonata_dir(self) -> Path:
        return self.resources_dir / "jsonata"

    @property
    def schema_dir(self) -> Path:
        return self.resources_dir / "schema" / "xml"

    # ------------------------------------------------------------------
    # Readiness check
    # ------------------------------------------------------------------

    def is_populated(self, version: str = "4-0") -> CacheStatus:
        """Check whether all pre-fetchable resources are present.

        This performs only local file-existence checks — no network calls,
        no API key needed.  It returns quickly in all cases.

        Args:
            version: USDM version string (e.g. ``"4-0"``).

        Returns:
            A :class:`CacheStatus` describing what is present and what is
            missing.
        """
        missing: list[str] = []

        has_resources = self._has_jsonata_resources() and self._has_xsd_resources()
        if not self._has_jsonata_resources():
            missing.append("JSONata custom function files")
        if not self._has_xsd_resources():
            missing.append("XSD schema files")

        has_rules = self._has_rules(version)
        if not has_rules:
            missing.append(f"USDM validation rules (version {version})")

        has_ct_index = self._has_ct_index()
        if not has_ct_index:
            missing.append("CT package index")

        return CacheStatus(
            ready=len(missing) == 0,
            has_resources=has_resources,
            has_rules=has_rules,
            has_ct_index=has_ct_index,
            cache_dir=str(self._cache_dir),
            details=missing,
        )

    def _has_jsonata_resources(self) -> bool:
        return self.jsonata_dir.exists() and any(self.jsonata_dir.glob("*.jsonata"))

    def _has_xsd_resources(self) -> bool:
        sentinel = self.schema_dir / "cdisc-usdm-xhtml-1.0" / "usdm-xhtml-1.0.xsd"
        return sentinel.exists()

    def _has_rules(self, version: str) -> bool:
        rules_file = self._cache_dir / "rules" / "usdm" / f"{version}.json"
        return rules_file.exists()

    def _has_ct_index(self) -> bool:
        ct_file = self._cache_dir / "ct" / "published_packages.json"
        return ct_file.exists()

    # ------------------------------------------------------------------
    # Prepare / update
    # ------------------------------------------------------------------

    def prepare(
        self,
        version: str = "4-0",
        api_key: Optional[str] = None,
    ) -> CacheStatus:
        """Download all resources needed for USDM CORE validation.

        Returns immediately if the cache is already fully populated.
        Otherwise downloads only the missing pieces:

        1. JSONata and XSD files are fetched from GitHub (no API key).
        2. USDM validation rules and the CT package index are fetched
           from the CDISC Library API (requires *api_key*).

        CT codelist data for specific ``codeSystemVersion`` values used
        in a file is *not* pre-fetched here — it is downloaded on demand
        during validation because the required versions vary per file.

        Args:
            version: USDM version string (e.g. ``"4-0"``).
            api_key: CDISC Library API key.  If ``None``, falls back to
                the ``CDISC_LIBRARY_API_KEY`` environment variable.

        Returns:
            A :class:`CacheStatus` reflecting the state of the cache
            after the operation.
        """
        status = self.is_populated(version)
        if status.ready:
            logger.info("CORE cache is already populated at %s", self._cache_dir)
            return status

        # Resolve the API key
        resolved_key = api_key or os.environ.get(
            "CDISC_LIBRARY_API_KEY", ""
        )

        # --- GitHub resources (no API key needed) -------------------------
        if not status.has_resources:
            logger.info("Downloading resource files from GitHub ...")
            self._ensure_jsonata_resources()
            self._ensure_xsd_schema_resources()

        # --- CDISC Library resources (API key needed) ---------------------
        if not status.has_rules or not status.has_ct_index:
            if not resolved_key:
                logger.warning(
                    "CDISC Library API key not available. Set the "
                    "CDISC_LIBRARY_API_KEY environment variable or pass "
                    "api_key to download rules and CT data."
                )
            else:
                self._prepare_api_resources(version, resolved_key)

        return self.is_populated(version)

    def _prepare_api_resources(self, version: str, api_key: str) -> None:
        """Download rules and CT index from the CDISC Library API."""
        # Deferred import to avoid import-time side effects
        from cdisc_rules_engine.config import config
        from cdisc_rules_engine.services.cache import CacheServiceFactory
        from cdisc_rules_engine.services.cdisc_library_service import (
            CDISCLibraryService,
        )
        from cdisc_rules_engine.constants.cache_constants import PUBLISHED_CT_PACKAGES
        from cdisc_rules_engine.utilities.utils import get_rules_cache_key

        # Ensure the env var is set for the library service
        if "CDISC_LIBRARY_API_KEY" not in os.environ:
            os.environ["CDISC_LIBRARY_API_KEY"] = api_key

        cache = CacheServiceFactory(config).get_cache_service()
        library_service = CDISCLibraryService(api_key, cache)

        # --- Rules ---
        if not self._has_rules(version):
            logger.info("Downloading USDM validation rules (version %s) ...", version)
            try:
                cache_key = get_rules_cache_key("usdm", version)
                result = library_service.get_rules_by_catalog("usdm", version)
                rules = (
                    result.get("rules", [])
                    if isinstance(result, dict)
                    else result
                )
                self.cache_rules("usdm", version, rules)
                logger.info("Cached %d rules", len(rules))
            except Exception as e:
                logger.warning("Failed to download rules: %s", e)

        # --- CT package index ---
        if not self._has_ct_index():
            logger.info("Downloading CT package index ...")
            try:
                packages = library_service.get_all_ct_packages()
                ct_packages = [
                    package.get("href", "").split("/")[-1]
                    for package in packages
                ]
                cache.add(PUBLISHED_CT_PACKAGES, ct_packages)
                self.cache_ct_packages(ct_packages)
                logger.info("Cached %d CT package names", len(ct_packages))
            except Exception as e:
                logger.warning("Failed to download CT package index: %s", e)

    # ------------------------------------------------------------------
    # Resource downloads (GitHub — no API key)
    # ------------------------------------------------------------------

    def ensure_resources(self) -> None:
        """
        Download JSONata and XSD resources if not already present.

        This is called automatically during validation but can also be
        called independently.  No API key is required — the files are
        fetched from GitHub.
        """
        self._ensure_jsonata_resources()
        self._ensure_xsd_schema_resources()

    def _ensure_jsonata_resources(self) -> None:
        """Download JSONata custom function files if not present."""
        if self._has_jsonata_resources():
            return

        self.jsonata_dir.mkdir(parents=True, exist_ok=True)
        for resource_path in _JSONATA_FILES:
            filename = resource_path.split("/")[-1]
            filepath = self.jsonata_dir / filename
            url = f"{_GITHUB_RAW_BASE}/{resource_path}"
            try:
                logger.info("Downloading %s", url)
                urllib.request.urlretrieve(url, filepath)
            except Exception as e:
                logger.warning("Failed to download %s: %s", url, e)

    def _ensure_xsd_schema_resources(self) -> None:
        """Download XSD schema files if not present."""
        if self._has_xsd_resources():
            return

        # Create subdirectories
        (self.schema_dir / "cdisc-usdm-xhtml-1.0").mkdir(parents=True, exist_ok=True)
        (self.schema_dir / "xhtml-1.1").mkdir(parents=True, exist_ok=True)

        all_files = _USDM_XHTML_SCHEMA_FILES + _XHTML_SCHEMA_FILES
        for resource_path in all_files:
            # resource_path is like "resources/schema/xml/xhtml-1.1/foo.xsd"
            # We need the relative part after "resources/schema/xml/"
            relative = resource_path.replace("resources/schema/xml/", "")
            filepath = self.schema_dir / relative
            url = f"{_GITHUB_RAW_BASE}/{resource_path}"
            try:
                urllib.request.urlretrieve(url, filepath)
            except Exception:
                # Some files may not exist but continue - not all are critical
                pass

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all cached resources. They will be re-downloaded on next use."""
        import shutil

        if self._cache_dir.exists():
            shutil.rmtree(self._cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Disk cache: rules
    # ------------------------------------------------------------------

    def cache_rules(self, standard: str, version: str, rules: list) -> None:
        """
        Persist downloaded rules to disk cache so they survive process restarts.

        Args:
            standard: The standard name (e.g. "usdm")
            version: The version (e.g. "4-0")
            rules: List of rule dicts from CDISC Library
        """
        rules_dir = self._cache_dir / "rules" / standard
        rules_dir.mkdir(parents=True, exist_ok=True)
        rules_file = rules_dir / f"{version}.json"
        with open(rules_file, "w", encoding="utf-8") as f:
            json.dump(rules, f)

    def load_cached_rules(self, standard: str, version: str) -> Optional[list]:
        """
        Load rules from the disk cache.

        Args:
            standard: The standard name (e.g. "usdm")
            version: The version (e.g. "4-0")

        Returns:
            List of rule dicts, or None if not cached.
        """
        rules_file = self._cache_dir / "rules" / standard / f"{version}.json"
        if not rules_file.exists():
            return None
        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    # ------------------------------------------------------------------
    # Disk cache: CT packages
    # ------------------------------------------------------------------

    def cache_ct_packages(self, packages: list) -> None:
        """
        Persist the list of published CT package names to disk.

        Args:
            packages: List of CT package name strings
        """
        ct_dir = self._cache_dir / "ct"
        ct_dir.mkdir(parents=True, exist_ok=True)
        ct_file = ct_dir / "published_packages.json"
        with open(ct_file, "w", encoding="utf-8") as f:
            json.dump(packages, f)

    def load_cached_ct_packages(self) -> Optional[list]:
        """
        Load the list of published CT packages from disk cache.

        Returns:
            List of package name strings, or None if not cached.
        """
        ct_file = self._cache_dir / "ct" / "published_packages.json"
        if not ct_file.exists():
            return None
        try:
            with open(ct_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def cache_ct_package_data(self, package_name: str, data: dict) -> None:
        """
        Persist CT package codelist data to disk.

        Args:
            package_name: Package name (e.g. "sdtmct-2025-09-26")
            data: The codelist terms map data
        """
        ct_data_dir = self._cache_dir / "ct" / "data"
        ct_data_dir.mkdir(parents=True, exist_ok=True)
        # Use a safe filename
        safe_name = package_name.replace("/", "_")
        ct_file = ct_data_dir / f"{safe_name}.json"
        with open(ct_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load_cached_ct_package_data(self, package_name: str) -> Optional[dict]:
        """
        Load CT package codelist data from disk cache.

        Args:
            package_name: Package name (e.g. "sdtmct-2025-09-26")

        Returns:
            The codelist terms map data, or None if not cached.
        """
        safe_name = package_name.replace("/", "_")
        ct_file = self._cache_dir / "ct" / "data" / f"{safe_name}.json"
        if not ct_file.exists():
            return None
        try:
            with open(ct_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
