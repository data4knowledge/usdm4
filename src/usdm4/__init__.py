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
from usdm4.core.core_validation_result import CoreValidationResult


class USDM4:
    MODULE = "usdm4.USDM4"

    def __init__(self):
        self.root = self._root_path()
        self.validator = RulesValidation4(self.root)
        self._core_validator: Optional[CoreValidator] = None

    def validate(self, file_path: str) -> RulesValidationResults:
        return self.validator.validate(file_path)

    def validate_core(
        self,
        file_path: str,
        version: str = "4-0",
        cache_dir: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> CoreValidationResult:
        """
        Validate a USDM JSON file using the CDISC Rules Engine (CORE).

        Runs the full set of CDISC CORE conformance rules against the file.
        This may take several minutes. For non-blocking execution, use
        :meth:`validate_core_async` instead.

        Args:
            file_path: Path to the USDM JSON file.
            version: USDM version (``"3-0"`` or ``"4-0"``). Default ``"4-0"``.
            cache_dir: Optional path to the cache directory for downloaded
                resources. If None, uses ``~/.cache/usdm4/core/``.
            api_key: Optional CDISC Library API key. If None, reads from
                ``CDISC_LIBRARY_API_KEY`` or ``CDISC_API_KEY`` environment variable.

        Returns:
            A :class:`~usdm4.core.CoreValidationResult` with findings.
        """
        validator = self._get_core_validator(cache_dir, api_key)
        return validator.validate(file_path, version=version)

    def validate_core_async(
        self,
        file_path: str,
        version: str = "4-0",
        cache_dir: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Future:
        """
        Validate a USDM JSON file using CDISC CORE in a background thread.

        Returns immediately with a ``Future[CoreValidationResult]``.

        Args:
            file_path: Path to the USDM JSON file.
            version: USDM version (``"3-0"`` or ``"4-0"``). Default ``"4-0"``.
            cache_dir: Optional path to the cache directory.
            api_key: Optional CDISC Library API key.

        Returns:
            A ``Future`` whose ``.result()`` returns a
            :class:`~usdm4.core.CoreValidationResult`.
        """
        validator = self._get_core_validator(cache_dir, api_key)
        return validator.validate_async(file_path, version=version)

    def _get_core_validator(
        self, cache_dir: Optional[str] = None, api_key: Optional[str] = None
    ) -> CoreValidator:
        """Get or create the CoreValidator instance."""
        if self._core_validator is None or cache_dir is not None or api_key is not None:
            self._core_validator = CoreValidator(
                cache_dir=cache_dir, api_key=api_key
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
