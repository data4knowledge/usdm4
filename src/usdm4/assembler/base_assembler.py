from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.builder.builder import Builder


class BaseAssembler:
    MODULE = "usdm4.assembler.base_assembler.BaseAssembler"

    def __init__(self, builder: Builder, errors: Errors):
        self._errors = errors
        self._builder = builder

    def execute(self, data: dict) -> None:
        pass
