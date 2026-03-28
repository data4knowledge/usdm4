import json
import pathlib
from concurrent.futures import Future
from typing import Optional
from typing_extensions import deprecated
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.rules.rules_validation import RulesValidation4
from usdm3.rules.rules_validation_results import RulesValidationResults
from usdm4.api.wrapper import Wrapper
from usdm4.convert.convert import Convert
from usdm4.builder.builder import Builder
from usdm4.assembler.assembler import Assembler
from usdm4.core.core_validator import CoreValidator
from usdm4.core.core_cache_manager import CoreCacheManager, CacheStatus


class USDM4:
    MODULE = "usdm4.USDM4"

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialise the USDM4 facade.

        Args:
            cache_dir: Optional path to the cache directory used by CDISC
                CORE validation. If None, a platform-appropriate default is
                used (see :func:`~usdm4.core.core_cache_manager.default_cache_dir`).
                Pass an explicit path for web-server deployments where the
                default user-level cache may not be appropriate.
        """
        self.root = self._root_path()
        self.validator = RulesValidation4(self.root)
        self._cache_dir = cache_dir
        self._core_validator: Optional[CoreValidator] = None

    def validate(self, file_path: str) -> RulesValidationResults:
        return self.validator.validate(file_path)

    def validate_core(
        self,
        file_path: str,
        version: str = "4-0",
        cache_dir: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Errors:
        """
        Validate a USDM JSON file using the CDISC Rules Engine (CORE).

        Runs the full set of CDISC CORE conformance rules against the file.
        This may take several minutes. For non-blocking execution, use
        :meth:`validate_core_async` instead.

        Args:
            file_path: Path to the USDM JSON file.
            version: USDM version (``"3-0"`` or ``"4-0"``). Default ``"4-0"``.
            cache_dir: Optional path to the cache directory for downloaded
                resources. If None, uses the instance-level cache_dir or a
                platform-appropriate default.
            api_key: Optional CDISC Library API key. If None, reads from
                ``CDISC_LIBRARY_API_KEY`` or ``CDISC_API_KEY`` environment variable.

        Returns:
            An :class:`~simple_error_log.errors.Errors` instance with findings.
        """
        validator = self._get_core_validator(cache_dir, api_key)
        result = validator.validate(file_path, version=version)
        return result.to_errors()

    def validate_core_async(
        self,
        file_path: str,
        version: str = "4-0",
        cache_dir: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Future:
        """
        Validate a USDM JSON file using CDISC CORE in a background thread.

        Returns immediately with a ``Future[Errors]``.

        Args:
            file_path: Path to the USDM JSON file.
            version: USDM version (``"3-0"`` or ``"4-0"``). Default ``"4-0"``.
            cache_dir: Optional path to the cache directory.
            api_key: Optional CDISC Library API key.

        Returns:
            A ``Future`` whose ``.result()`` returns an
            :class:`~simple_error_log.errors.Errors` instance.
        """
        validator = self._get_core_validator(cache_dir, api_key)
        future = validator.validate_async(file_path, version=version)
        # Wrap the future to convert CoreValidationResult -> Errors
        wrapped = Future()

        def _on_done(f):
            try:
                result = f.result()
                wrapped.set_result(result.to_errors())
            except Exception as e:
                wrapped.set_exception(e)

        future.add_done_callback(_on_done)
        return wrapped

    def prepare_core(
        self,
        version: str = "4-0",
        api_key: Optional[str] = None,
    ) -> CacheStatus:
        """
        Pre-populate the CDISC CORE validation cache.

        Downloads rules, CT index, JSONata files, and XSD schemas that are
        not already cached. Returns immediately if everything is present.
        Call this at application startup (e.g. in a web server's ``on_startup``
        hook) to avoid first-request latency.

        Args:
            version: USDM version string (``"3-0"`` or ``"4-0"``).
            api_key: Optional CDISC Library API key. If None, reads from the
                ``CDISC_LIBRARY_API_KEY`` or ``CDISC_API_KEY`` environment variable.

        Returns:
            A :class:`~usdm4.core.core_cache_manager.CacheStatus` indicating
            what is cached.
        """
        validator = self._get_core_validator(api_key=api_key)
        return validator.cache_manager.prepare(version=version, api_key=api_key)

    def core_cache_status(self, version: str = "4-0") -> CacheStatus:
        """
        Quick check of cache readiness (no network calls).

        Args:
            version: USDM version string.

        Returns:
            A :class:`~usdm4.core.core_cache_manager.CacheStatus`.
        """
        cache_manager = CoreCacheManager(self._cache_dir)
        return cache_manager.is_populated(version=version)

    def _get_core_validator(
        self, cache_dir: Optional[str] = None, api_key: Optional[str] = None
    ) -> CoreValidator:
        """Get or create the CoreValidator instance."""
        effective_cache_dir = cache_dir or self._cache_dir
        if self._core_validator is None or cache_dir is not None or api_key is not None:
            self._core_validator = CoreValidator(
                cache_dir=effective_cache_dir, api_key=api_key
            )
        return self._core_validator

    def convert(self, file_path: str) -> Wrapper:
        with open(file_path, "r") as file:
            data = json.load(file)
        return Convert.convert(data)

    def builder(self, errors: Errors) -> Builder:
        return Builder(self.root, errors)

    def assembler(self, errors: Errors) -> Assembler:
        return Assembler(self.root, errors)

    def minimum(
        self, study_name: str, sponsor_id: str, version: str, errors: Errors
    ) -> Wrapper:
        return Builder(self.root, errors).minimum(study_name, sponsor_id, version)

    @deprecated("Use the 'load' or the 'loadd' methods")
    def from_json(self, data: dict) -> Wrapper:
        return Wrapper.model_validate(data)

    def loadd(self, data: dict, errors: Errors) -> Wrapper | None:
        try:
            return Wrapper.model_validate(data)
        except Exception as e:
            errors.exception(
                "Failed to load a dict into USDM",
                e,
                KlassMethodLocation(self.MODULE, "from_dict"),
            )
            return None

    def load(self, filepath: str, errors: Errors) -> Wrapper | None:
        try:
            data = None
            with open(filepath, "r") as f:
                data = json.load(f)
                f.close()
            return Wrapper.model_validate(data)
        except Exception as e:
            errors.exception(
                "Failed to load file '{filepath}' into USDM",
                e,
                KlassMethodLocation(self.MODULE, "load"),
            )
            return None

    def _root_path(self) -> str:
        return pathlib.Path(__file__).parent.resolve()
