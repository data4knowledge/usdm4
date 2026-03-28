"""Tests for the USDM4 facade's CORE cache integration methods."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from usdm4 import USDM4
from usdm4.core.core_cache_manager import CacheStatus, default_cache_dir


class TestUSDM4CacheDir:
    """Test the cache_dir parameter on USDM4.__init__."""

    def test_default_no_cache_dir(self):
        """Without cache_dir, _cache_dir should be None (deferred to platformdirs)."""
        u = USDM4()
        assert u._cache_dir is None

    def test_custom_cache_dir(self, tmp_path):
        """Explicit cache_dir is stored and propagated."""
        custom = str(tmp_path / "my_cache")
        u = USDM4(cache_dir=custom)
        assert u._cache_dir == custom


class TestCoreCacheStatus:
    """Test the core_cache_status convenience method."""

    def test_returns_cache_status(self, tmp_path):
        custom = str(tmp_path / "my_cache")
        u = USDM4(cache_dir=custom)
        status = u.core_cache_status()
        assert isinstance(status, CacheStatus)
        assert status.cache_dir == custom

    def test_empty_cache_not_ready(self, tmp_path):
        custom = str(tmp_path / "empty_cache")
        u = USDM4(cache_dir=custom)
        status = u.core_cache_status()
        assert status.ready is False

    def test_version_forwarded(self, tmp_path):
        custom = str(tmp_path / "cache")
        u = USDM4(cache_dir=custom)
        status = u.core_cache_status(version="3-0")
        # Version is forwarded — we just check it returns without error
        assert isinstance(status, CacheStatus)


class TestPrepareCoreMethod:
    """Test the prepare_core facade method."""

    def test_returns_cache_status(self, tmp_path):
        """prepare_core should return a CacheStatus."""
        custom = str(tmp_path / "prep_cache")
        u = USDM4(cache_dir=custom)

        # Patch _prepare_api_resources to avoid real network calls
        with patch(
            "usdm4.core.core_cache_manager.CoreCacheManager._prepare_api_resources"
        ):
            status = u.prepare_core(version="4-0")

        assert isinstance(status, CacheStatus)

    def test_propagates_cache_dir(self, tmp_path):
        """The cache_dir from __init__ should be used by prepare_core."""
        custom = str(tmp_path / "prop_cache")
        u = USDM4(cache_dir=custom)

        with patch(
            "usdm4.core.core_cache_manager.CoreCacheManager._prepare_api_resources"
        ):
            status = u.prepare_core()

        assert status.cache_dir == custom


class TestGetCoreValidator:
    """Test _get_core_validator with cache_dir propagation."""

    def test_inherits_instance_cache_dir(self, tmp_path):
        custom = str(tmp_path / "inherit")
        u = USDM4(cache_dir=custom)
        validator = u._get_core_validator()
        assert validator.cache_manager.cache_dir == Path(custom)

    def test_method_cache_dir_overrides(self, tmp_path):
        """cache_dir passed to validate_core should override the instance level."""
        instance_dir = str(tmp_path / "instance")
        method_dir = str(tmp_path / "method")
        u = USDM4(cache_dir=instance_dir)

        # Get validator with method-level override
        validator = u._get_core_validator(cache_dir=method_dir)
        assert validator.cache_manager.cache_dir == Path(method_dir)


class TestCoreExports:
    """Verify that the core subpackage exports all new public symbols."""

    def test_cache_status_exported(self):
        from usdm4.core import CacheStatus
        assert CacheStatus is not None

    def test_default_cache_dir_exported(self):
        from usdm4.core import default_cache_dir
        assert callable(default_cache_dir)

    def test_core_cache_manager_exported(self):
        from usdm4.core import CoreCacheManager
        assert CoreCacheManager is not None

    def test_core_validator_exported(self):
        from usdm4.core import CoreValidator
        assert CoreValidator is not None

    def test_core_validation_result_exported(self):
        from usdm4.core import CoreValidationResult
        assert CoreValidationResult is not None
