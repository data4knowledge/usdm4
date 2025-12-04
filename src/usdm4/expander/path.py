import json
from simple_error_log import Errors
from .timepoint import Timepoint
from .decision import Decision
from .exit import Exit

class Path():

    def __init__(self, errors: Errors):
        self._timepoints: list[Timepoint] = []
        self._end_marker = None
        self._errors = errors

    def add(self, item: Timepoint | Decision | Exit):
        if isinstance(item, Timepoint):
            self._timepoints.append(item)
        elif isinstance(item, Decision):
            self._errors.info(f"Adding a decision node!!!")
        elif isinstance(item, Exit):
            self._end_marker = item
        else:
            self._errors.error(f"Attempt to add unknown inten to a path, '{item}'")

    def to_json(self) -> str:
        result = {}
        result["timepoints"] = [x.to_dict() for x in self._timepoints]
        result["end_marker"] = self._end_marker._to_dict() if self._end_marker else None
        result["decision"] = None
        return json.dumps(result, indent=4)
