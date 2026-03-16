"""
Cache manager for CDISC CORE validation resources.

Manages a configurable cache directory for storing downloaded resources
(JSONata files, XSD schemas, rules, CT packages) so they persist across
validation runs and package upgrades.
"""

import hashlib
import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default cache location: ~/.cache/usdm4/core/ (or platform equivalent)
_DEFAULT_CACHE_DIR = Path.home() / ".cache" / "usdm4" / "core"

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


class CoreCacheManager:
    """
    Manages the local cache directory for CDISC CORE validation resources.

    Resources cached include:
    - JSONata custom function files
    - XSD schema files (USDM XHTML + XHTML 1.1)
    - Validation rules (cached by the CDISC Rules Engine itself)
    - CT package data (cached by the CDISC Rules Engine itself)

    The cache directory is configurable. By default it uses
    ~/.cache/usdm4/core/ which survives package upgrades.

    Args:
        cache_dir: Path to the cache directory. If None, uses the default.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is not None:
            self._cache_dir = Path(cache_dir)
        else:
            self._cache_dir = _DEFAULT_CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)

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

    def ensure_resources(self) -> None:
        """
        Download all required resources if not already present in the cache.

        This includes JSONata custom functions and XSD schema files that are
        not included in the cdisc-rules-engine pip package.
        """
        self._ensure_jsonata_resources()
        self._ensure_xsd_schema_resources()

    def _ensure_jsonata_resources(self) -> None:
        """Download JSONata custom function files if not present."""
        if self.jsonata_dir.exists() and any(self.jsonata_dir.glob("*.jsonata")):
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
        sentinel = self.schema_dir / "cdisc-usdm-xhtml-1.0" / "usdm-xhtml-1.0.xsd"
        if sentinel.exists():
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

    def clear(self) -> None:
        """Remove all cached resources. They will be re-downloaded on next use."""
        import shutil
        if self._cache_dir.exists():
            shutil.rmtree(self._cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

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
